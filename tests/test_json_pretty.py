"""One-off test: verify ask_json returns a clean dict and pretty-print it."""
import json
from app.models.llm import ask_json

result = ask_json("Give me 3 colors as a JSON object with key 'colors' (list of hex strings).")
print(json.dumps(result, indent=2))