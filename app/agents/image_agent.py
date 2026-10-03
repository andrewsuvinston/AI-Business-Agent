"""Image generation + upscaling. Two providers only: Cloudflare + ComfyUI upscale."""
import base64
import json
import random
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import requests

from config import settings

COMFY_HOST = settings.COMFYUI_HOST
UPSCALE_MODEL_NAME = "RealESRGAN_x2plus.pth"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = PROJECT_ROOT / "data" / "processed" / "images"


# ---------------------------------------------------------------------------
# Image generation via Cloudflare Workers AI (FLUX.1-schnell)
# ---------------------------------------------------------------------------

CLOUDFLARE_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{acct}"
    "/ai/run/@cf/black-forest-labs/flux-1-schnell"
)


def generate(prompt: str, seed: int | None = None,
             output_dir: Path | None = None, **_ignored) -> Path:
    """Generate one 1024x1024 image via Cloudflare Workers AI."""
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    out_dir = Path(output_dir) if output_dir else IMAGES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    acct = settings.CLOUDFLARE_ACCOUNT_ID
    token = settings.CLOUDFLARE_API_TOKEN
    if not acct or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN missing in .env")

    url = CLOUDFLARE_URL.format(acct=acct)
    payload = {"prompt": prompt, "steps": 4}

    print(f"  [cloudflare] FLUX.1-schnell -> 1024x1024 ...")
    t0 = time.time()
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload, timeout=180,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Cloudflare error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Cloudflare returned error: {data}")

    img_bytes = base64.b64decode(data["result"]["image"])
    dest = out_dir / f"image_{seed:010d}.png"
    dest.write_bytes(img_bytes)
    print(f"  [cloudflare] done in {time.time()-t0:.1f}s -> {dest.name}")
    return dest


# ---------------------------------------------------------------------------
# Upscale via local ComfyUI (Real-ESRGAN x2)
# ---------------------------------------------------------------------------

def _upscale_workflow(server_filename: str, target_size: int) -> dict:
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


def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))


def _upload_image(path: Path) -> str:
    boundary = "----comfy" + uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'.encode(),
        b"Content-Type: image/png\r\n\r\n",
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        f"{COMFY_HOST}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))["name"]


def upscale_via_comfy(src: Path, target_size: int = 2000) -> Path:
    """Upscale via ComfyUI's Real-ESRGAN. Returns path to upscaled PNG."""
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    print(f"  [upscale] uploading {src.name} to ComfyUI...")
    server_name = _upload_image(src)
    resp = _post_json(f"{COMFY_HOST}/prompt",
                      {"prompt": _upscale_workflow(server_name, target_size)})
    prompt_id = resp["prompt_id"]
    print(f"  [upscale] queued prompt_id={prompt_id}")

    start = time.time()
    while True:
        try:
            history = _get_json(f"{COMFY_HOST}/history/{prompt_id}")
            if prompt_id in history:
                break
        except Exception as e:
            print(f"  [upscale] (poll hiccup: {e})")
        print(f"  [upscale] still upscaling... {int(time.time() - start)}s")
        time.sleep(5)

    outputs = history[prompt_id]["outputs"]
    image_info = next((n["images"][0] for n in outputs.values()
                       if n.get("images")), None)
    if image_info is None:
        raise RuntimeError(f"No image in ComfyUI output: {outputs}")

    qs = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    })
    dest = src.with_name(src.stem + f"_upscaled_{target_size}.png")
    with urllib.request.urlopen(f"{COMFY_HOST}/view?{qs}", timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"  [upscale] saved -> {dest}")
    return dest