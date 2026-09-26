"""Entry point for the AI Business Agent.

Commands:
    python -m app.main "any question"                       # free-text mode
    python -m app.main ideas "<direction>" [--count N] [--model M]
    python -m app.main report
"""
import sys

from app.models.llm import ask
from app.workflows import idea_workflow, report_workflow

USAGE = '''Usage:
  python -m app.main "your question here"
  python -m app.main ideas "<direction>" [--count N] [--model MODEL]
  python -m app.main report

Options for `ideas`:
  --count N       number of ideas to generate (default 5)
  --model NAME    override the model from .env for this run

Examples:
  python -m app.main "What is machine learning?"
  python -m app.main ideas "printable wall art for engineering students" --count 5
  python -m app.main ideas "space posters" --model qwen2.5-coder:7b
  python -m app.main report
'''


def _pop_flag(args: list[str], flag: str) -> tuple[list[str], str | None]:
    if flag not in args:
        return args, None
    i = args.index(flag)
    if i + 1 >= len(args):
        print(f"Error: {flag} needs a value after it.")
        raise SystemExit(1)
    value = args[i + 1]
    remaining = args[:i] + args[i + 2:]
    return remaining, value


def _parse_idea_args(args: list[str]) -> tuple[str, int, str | None]:
    args, count_raw = _pop_flag(args, "--count")
    count = 5
    if count_raw is not None:
        try:
            count = int(count_raw)
        except ValueError:
            print(f"Error: --count needs an integer. Got: {count_raw!r}")
            raise SystemExit(1)
    args, model = _pop_flag(args, "--model")
    return " ".join(args).strip(), count, model


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(USAGE)
        return

    if args[0] == "ideas":
        direction, count, model = _parse_idea_args(args[1:])
        if not direction:
            print("Error: no direction given.")
            print(USAGE)
            return
        idea_workflow.run(direction=direction, count=count, model=model)
        return

    if args[0] == "report":
        report_workflow.run()
        return

    prompt = " ".join(args)
    print(f"\n>>> Prompt: {prompt}\n")
    print("--- Local model reply ---")
    print(ask(prompt))


if __name__ == "__main__":
    main()
