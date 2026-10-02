"""Entry point for the AI Business Agent.

Commands:
    python -m app.main "any question"
    python -m app.main ideas "<direction>" [--count N] [--model M]
    python -m app.main metadata <ideas_file> [--index N | --all] [--model M]
    python -m app.main image <ideas_file> [--index N | --all]
    python -m app.main enhance <ideas_file> [--index N | --all]
    python -m app.main quality <ideas_file> [--index N | --all]
    python -m app.main run <ideas_file> [--index N | --all] [--model M] [--force]
    python -m app.main qc
    python -m app.main report
"""
import sys
from pathlib import Path

from app.models.llm import ask
from app.utils.storage import load_json
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
  python -m app.main metadata <ideas_file> [--index N | --all] [--model MODEL]
  python -m app.main image <ideas_file> [--index N | --all]
  python -m app.main enhance <ideas_file> [--index N | --all]
  python -m app.main quality <ideas_file> [--index N | --all]
  python -m app.main run <ideas_file> [--index N | --all] [--model MODEL] [--force]
  python -m app.main qc
  python -m app.main report
'''


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

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


def _pop_bool_flag(args: list[str], flag: str) -> tuple[list[str], bool]:
    if flag not in args:
        return args, False
    i = args.index(flag)
    return args[:i] + args[i + 1:], True


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


def _parse_metadata_args(args: list[str]) -> tuple[str, int, str | None, bool]:
    args, all_flag = _pop_bool_flag(args, "--all")
    args, index_raw = _pop_flag(args, "--index")
    index = 1
    if index_raw is not None:
        try:
            index = int(index_raw)
        except ValueError:
            print(f"Error: --index needs an integer. Got: {index_raw!r}")
            raise SystemExit(1)
    args, model = _pop_flag(args, "--model")
    return " ".join(args).strip(), index, model, all_flag


# ---------------------------------------------------------------------------
# Batch helper — loop every idea in a file
# ---------------------------------------------------------------------------

def _for_each_idea(ideas_path: str, fn) -> None:
    """Call fn(index=i) for i in 1..N. Continue past per-idea failures."""
    data = load_json(Path(ideas_path))
    ideas = data.get("ideas", [])
    total = len(ideas)
    if total == 0:
        print(f"No ideas in {ideas_path}")
        return

    succeeded = 0
    skipped = 0
    failed = 0
    for i in range(1, total + 1):
        print(f"\n--- idea {i}/{total} ---")
        try:
            result = fn(index=i)
            if result == "skipped":
                skipped += 1
            else:
                succeeded += 1
        except Exception as e:
            failed += 1
            print(f"[error] idea #{i} failed: {e}")

    print(f"\n[done] {succeeded} done, {skipped} skipped, {failed} failed (of {total})")


# ---------------------------------------------------------------------------
# `run` command — the full pipeline for one idea
# ---------------------------------------------------------------------------

def _pipeline(ideas_file: str, index: int, model: str | None, force: bool = False):
    # Skip-guard: if this idea already produced a stock image, skip unless --force
    if not force:
        data = load_json(Path(ideas_file))
        ideas = data.get("ideas", [])
        if 1 <= index <= len(ideas):
            stock = ideas[index - 1].get("image_stock_path")
            if stock and Path(stock).exists():
                print(f"[skip] idea #{index} already has stock image")
                print(f"       {stock}")
                print(f"       (use --force to redo)")
                return "skipped"

    print(f"\n{'='*68}\n  PIPELINE — idea #{index}\n{'='*68}")
    print("\n[1/4] image")
    image_workflow.run(ideas_path=ideas_file, index=index)
    print("\n[2/4] enhance")
    enhance_workflow.run(ideas_path=ideas_file, index=index)
    print("\n[3/4] quality")
    quality_workflow.run(ideas_path=ideas_file, index=index)
    print("\n[4/4] metadata")
    metadata_workflow.run(ideas_file=ideas_file, index=index, model=model)
    print(f"\n[done] idea #{index} pipeline complete")
    return "done"


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

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
        ideas_file, index, model, all_flag = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        if all_flag:
            _for_each_idea(
                ideas_file,
                lambda index: metadata_workflow.run(
                    ideas_file=ideas_file, index=index, model=model
                ),
            )
        else:
            metadata_workflow.run(ideas_file=ideas_file, index=index, model=model)
        return

    if args[0] == "image":
        ideas_file, index, _, all_flag = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        if all_flag:
            _for_each_idea(
                ideas_file,
                lambda index: image_workflow.run(ideas_path=ideas_file, index=index),
            )
        else:
            image_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "enhance":
        ideas_file, index, _, all_flag = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        if all_flag:
            _for_each_idea(
                ideas_file,
                lambda index: enhance_workflow.run(ideas_path=ideas_file, index=index),
            )
        else:
            enhance_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "quality":
        ideas_file, index, _, all_flag = _parse_metadata_args(args[1:])
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        if all_flag:
            _for_each_idea(
                ideas_file,
                lambda index: quality_workflow.run(ideas_path=ideas_file, index=index),
            )
        else:
            quality_workflow.run(ideas_path=ideas_file, index=index)
        return

    if args[0] == "run":
        # --force is unique to `run`
        args_rest, force = _pop_bool_flag(args[1:], "--force")
        ideas_file, index, model, all_flag = _parse_metadata_args(args_rest)
        if not ideas_file:
            print("Error: no ideas file given.")
            print(USAGE)
            return
        if all_flag:
            _for_each_idea(
                ideas_file,
                lambda index: _pipeline(ideas_file, index, model, force=force),
            )
        else:
            _pipeline(ideas_file, index, model, force=force)
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