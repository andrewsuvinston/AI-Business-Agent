"""Entry point for the AI Business Agent.

Right now: takes a prompt from the command line, sends it to the local model,
prints the reply. Tomorrow this becomes the orchestrator that routes to agents.
"""
import sys

from app.models.llm import ask


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m app.main "your question here"')
        return

    prompt = " ".join(sys.argv[1:])
    print(f"\n>>> Prompt: {prompt}\n")
    print("--- Local model reply ---")
    reply = ask(prompt)
    print(reply)


if __name__ == "__main__":
    main()