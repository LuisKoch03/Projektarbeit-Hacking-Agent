"""Command-line entry point for the interactive agent."""

import argparse
import sys

from openai import OpenAIError

from .config import Settings
from .llm import create_agent


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Run the LangChain project agent.")
    parser.add_argument("prompt", nargs="?", help="Optional first message.")
    return parser


def main() -> int:
    """Run an interactive conversation until the user exits."""
    args = build_parser().parse_args()

    try:
        settings = Settings.from_env()
        agent = create_agent(settings)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1

    messages: list[dict[str, str]] = []
    prompt = args.prompt
    print("Chat started. Type 'exit' or 'quit' to stop.")

    while True:
        if prompt is None:
            try:
                prompt = input("You: ").strip()
            except EOFError:
                print()
                break

        if prompt.lower() in {"exit", "quit"}:
            break
        if not prompt:
            prompt = None
            continue

        messages.append({"role": "user", "content": prompt})
        try:
            result = agent.invoke({"messages": messages})
        except (OSError, OpenAIError) as error:
            messages.pop()
            print(f"Unable to contact API: {error}", file=sys.stderr)
            return 1

        response = result["messages"][-1]
        content = str(response.content)
        messages.append({"role": "assistant", "content": content})
        print(f"Assistant: {content}")
        prompt = None

    print("Chat ended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
