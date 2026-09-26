"""Central configuration. All settings come from .env (falling back to defaults)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = one folder above this file's parent folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from the project root, if it exists
load_dotenv(PROJECT_ROOT / ".env")

# --- Model settings ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# --- Data directories ---
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
READY_DIR = DATA_DIR / "ready_to_upload"
REJECTED_DIR = DATA_DIR / "rejected"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def ensure_dirs() -> None:
    """Create the data folders if they don't exist yet. Safe to call repeatedly."""
    for d in (RAW_DIR, PROCESSED_DIR, READY_DIR, REJECTED_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)