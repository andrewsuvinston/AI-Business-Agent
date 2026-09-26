"""Entry point for the AI Business Agent.

Commands:
    python -m app.main "any question"                 # free-text mode (old)
    python -m app.main ideas "wall art for students"   # structured ideas
    python -m app.main ideas "wall art for students" --count 3
"""
import sys

from app.models.llm import ask
from app.workflows import idea_workflow

USAGE = '''Usage:
  python -m app.main "your question here"
  python -m app.main ideas "<direction>" [--count N]

Examples:
  python -m app.main "What is machine learning?"
  python -m app.main ideas "printable wall art for engineering students" --count 5
'''


def _parse_idea_args(args: list[str]) -> tuple[str, int]:
    """Parse ['wall art', '--count', '5'] -> ('wall art', 5)."""
    count = 5
    if "--count" in args:
        i = args.index("--count")
        try:
            count = int(args[i + 1])
        except (IndexError, ValueError):
            print(f"Error: --count needs an integer after it. Got: {args[i+1:]}")
            raise SystemExit(1)
        args = args[:i] + args[i + 2:]
    return " ".join(args).strip(), count


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(USAGE)
        return

    if args[0] == "ideas":
        direction, count = _parse_idea_args(args[1:])
        if not direction:
            print("Error: no direction given.")
            print(USAGE)
            return
        idea_workflow.run(direction=direction, count=count)
        return

    # Default: free-text mode
    prompt = " ".join(args)
    print(f"\n>>> Prompt: {prompt}\n")
    print("--- Local model reply ---")
    print(ask(prompt))


if __name__ == "__main__":
    main()
