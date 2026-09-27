"""Image generation agent — talks to a local ComfyUI server over HTTP.

Requires:
    - ComfyUI running on COMFYUI_HOST (default http://127.0.0.1:8188)
    - An SD1.5 checkpoint loaded (v1-5-pruned-emaonly.safetensors)
"""

import json
import random
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from config import settings

COMFY_HOST = settings.COMFYUI_HOST
CHECKPOINT = "v1-5-pruned-emaonly.safetensors"

DEFAULT_NEGATIVE = "text, watermark, blurry, low quality, deformed, extra limbs"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = PROJECT_ROOT / "data" / "processed" / "images"


def _api_workflow(prompt: str, negative: str, width: int, height: int, seed: int) -> dict:
    """Return the workflow in ComfyUI's API (dict) format."""
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": CHECKPOINT}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {
                  "seed": seed, "steps": 20, "cfg": 7.5,
                  "sampler_name": "euler", "scheduler": "normal",
                  "denoise": 1.0,
                  "model": ["4", 0], "positive": ["6", 0],
                  "negative": ["7", 0], "latent_image": ["5", 0],
              }},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "ai_agent", "images": ["8", 0]}},
    }


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())


def generate(prompt: str,
             negative: str = DEFAULT_NEGATIVE,
             width: int = 512,
             height: int = 512,
             seed: int | None = None,
             output_dir: Path | None = None) -> Path:
    """Generate one image via ComfyUI. Returns the saved PNG path."""
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    out_dir = Path(output_dir) if output_dir else IMAGES_DIR
    client_id = str(uuid.uuid4())
    workflow = _api_workflow(prompt, negative, width, height, seed)

    # 1. queue the job
    resp = _post_json(f"{COMFY_HOST}/prompt",
                      {"prompt": workflow, "client_id": client_id})
    prompt_id = resp["prompt_id"]
    print(f"  queued prompt_id={prompt_id}  (seed={seed})")

    # 2. poll /history until this prompt_id shows up
    print("  waiting for ComfyUI to finish...")
    while True:
        history = _get_json(f"{COMFY_HOST}/history/{prompt_id}")
        if prompt_id in history:
            break
        time.sleep(3)

    outputs = history[prompt_id]["outputs"]

    # 3. find the SaveImage node's first image
    image_info = None
    for node in outputs.values():
        if "images" in node and node["images"]:
            image_info = node["images"][0]
            break
    if image_info is None:
        raise RuntimeError(f"No image in ComfyUI output: {outputs}")

    # 4. download it
    qs = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    })
    dest = out_dir / f"image_{seed:010d}.png"
    _download(f"{COMFY_HOST}/view?{qs}", dest)
    print(f"  saved -> {dest}")
    return dest
# ---------------------------------------------------------------------------
# Upscale via ComfyUI (uses Real-ESRGAN .pth model on CPU through torch)
# ---------------------------------------------------------------------------

UPSCALE_MODEL_NAME = "RealESRGAN_x4plus.pth"


def _upscale_workflow(server_filename: str, target_size: int = 2000) -> dict:
    """ComfyUI workflow in API format for 4x upscale + resize."""
    return {
        "1": {"class_type": "LoadImage",
              "inputs": {"image": server_filename}},
        "2": {"class_type": "UpscaleModelLoader",
              "inputs": {"model_name": UPSCALE_MODEL_NAME}},
        "3": {"class_type": "ImageUpscaleWithModel",
              "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "ImageScale",
              "inputs": {"image": ["3", 0],
                         "width": target_size, "height": target_size,
                         "upscale_method": "lanczos", "crop": "disabled"}},
        "5": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "upscaled", "images": ["4", 0]}},
    }


def _upload_image(path: Path) -> str:
    """Upload a local image to ComfyUI's input folder. Returns server filename."""
    boundary = "----comfy" + uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'.encode(),
        b"Content-Type: image/png\r\n\r\n",
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        f"{COMFY_HOST}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["name"]


def upscale_via_comfy(src: Path, target_size: int = 2000) -> Path:
    """Upscale src using ComfyUI's Real-ESRGAN node on CPU.

    Returns the path to the upscaled PNG saved next to src.
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    print(f"  [upscale] uploading {src.name} to ComfyUI...")
    server_name = _upload_image(src)

    wf = _upscale_workflow(server_name, target_size)
    resp = _post_json(f"{COMFY_HOST}/prompt", {"prompt": wf})
    prompt_id = resp["prompt_id"]
    print(f"  [upscale] queued prompt_id={prompt_id}")

    start = time.time()
    while True:
        try:
            history = _get_json(f"{COMFY_HOST}/history/{prompt_id}")
            if prompt_id in history:
                break
        except Exception as e:
            print(f"  [upscale] (poll hiccup: {e}) -- retrying")
        print(f"  [upscale] still upscaling... {int(time.time() - start)}s")
        time.sleep(5)

    outputs = history[prompt_id]["outputs"]
    image_info = None
    for node in outputs.values():
        if "images" in node and node["images"]:
            image_info = node["images"][0]
            break
    if image_info is None:
        raise RuntimeError(f"No image in ComfyUI upscale output: {outputs}")

    qs = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    })
    dest = src.with_name(src.stem + f"_upscaled_{target_size}.png")
    _download(f"{COMFY_HOST}/view?{qs}", dest)
    print(f"  [upscale] saved -> {dest}")
    return dest