"""Verify storage.save_json and load_json round-trip correctly."""
from app.utils.storage import save_json, load_json

sample = {
    "direction": "wall art for students",
    "ideas": [
        {"title": "Test Idea", "price": "Rs.99-299"},
        {"title": "Another Idea", "price": "Rs.149"},
    ],
}

saved_path = save_json(sample, "data/processed/test_storage.json")
print(f"Saved to: {saved_path}")
print(f"Exists:   {saved_path.exists()}")

loaded = load_json(saved_path)
print(f"Loaded:   {loaded}")

assert loaded == sample, "Round-trip failed!"
print("Round-trip OK")

missing = load_json("data/processed/does_not_exist.json")
assert missing is None, "Should have returned None for missing file"
print("Missing-file case OK")
