"""Central configuration. Minimal — only what's actually used."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- Providers ---
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "cloudflare").lower()
TEXT_PROVIDER = os.getenv("TEXT_PROVIDER", "ollama").lower()

# --- Cloudflare Workers AI (image generation) ---
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

# --- Ollama (local text generation) ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# --- ComfyUI (upscale) ---
COMFYUI_HOST = os.getenv("COMFYUI_HOST", "http://127.0.0.1:8188")

# --- Data directories ---
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
READY_DIR = DATA_DIR / "ready_to_upload"
REJECTED_DIR = DATA_DIR / "rejected"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, READY_DIR, REJECTED_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)