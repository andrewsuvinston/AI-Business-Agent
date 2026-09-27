"""Entry point for the AI Business Agent.

Commands:
    python -m app.main "any question"
    python -m app.main ideas "<direction>" [--count N] [--model M]
    python -m app.main metadata <ideas_file> [--index N] [--model M]
    python -m app.main image <ideas_file> [--index N]
    python -m app.main enhance <ideas_file> [--index N]
    python -m app.main quality <ideas_file> [--index N]
    python -m app.main qc
    python -m app.main report
"""
import sys

from app.models.llm import ask
from app.workflows import (
    enhance_workflow,
    idea_workflow,
    image_workflow,
    metadata_workflow,
    qc_workflow,
    quality_workflow,
    report_workflow,
)

USAGE = '''Usage:
  python -m app.main "your question here"
  python -m app.main ideas "<direction>" [--count N] [--model MODEL]
  python -m app.main metadata <ideas_file> [--index N] [--model MODEL]
  python -m app.main image <ideas_file> [--index N]
  python -m app.main enhance <ideas_file> [--index N]
  python -m app.main quality <ideas_file> [--index N]
  python -m app.main qc
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


def _parse_metadata_args(args: list[str]) -> tuple[str, int, str | None]:
    args, index_raw = _pop_flag(args, "--index")
    index = 1
    if index_raw is not None:
        try:
            index = int(index_raw)
        except ValueError:
            print(f"Error: --index needs an integer. Got: {index_raw!r}")
            raise SystemExit(1)
    args, model = _pop_flag(args, "--model")
    return " ".join(args).strip(), index, model


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

    if args[0] == "metadata":
        ideas_file, index, model = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        metadata_workflow.run(ideas_file=ideas_file, index=index, model=model)
        return

    if args[0] == "image":
        ideas_file, index, _ = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        image_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "enhance":
        ideas_file, index, _ = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        enhance_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "quality":
        ideas_file, index, _ = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        quality_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "qc":
        qc_workflow.run()
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