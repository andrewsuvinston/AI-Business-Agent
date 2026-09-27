"""Smoke test: generate one image via ComfyUI."""
from app.agents.image_agent import generate

if __name__ == "__main__":
    path = generate("a blue ceramic coffee mug on a wooden desk, soft light")
    print(f"OK -> {path}")