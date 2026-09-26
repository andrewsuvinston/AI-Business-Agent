"""Smoke test: run the Idea Agent once and print the result as a table."""
from app.agents.idea_agent import generate

result = generate("printable wall art for engineering students", count=3)

print(f"Direction: {result['direction']}")
print(f"Ideas returned: {len(result['ideas'])}")
print()

for i, idea in enumerate(result["ideas"], start=1):
    print(f"{i}. {idea['title']}")
    print(f"   Buyer:      {idea['buyer']}")
    print(f"   Format:     {idea['format']}")
    print(f"   Why:        {idea['why_it_might_sell']}")
    print(f"   Difficulty: {idea['difficulty']}")
    print(f"   Price:      {idea['price_range_inr']}")
    print(f"   Keywords:   {', '.join(idea['keywords'])}")
    print()
