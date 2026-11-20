"""Command-line entry point for the interactive agent."""

import argparse
from dataclasses import replace
import sys

from openai import BadRequestError, OpenAI, OpenAIError

from .config import Settings
from .llm import create_agent, ollama_model_capabilities


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Run the LangChain project agent.")
    parser.add_argument("prompt", nargs="?", help="Optional first message.")
    parser.add_argument("--model", help="Use this model without interactive selection.")
    return parser


def select_ollama_model(settings: Settings) -> Settings:
    """Let the user choose an installed model from Ollama's model list."""
    with OpenAI(api_key="ollama", base_url=settings.base_url, timeout=10, max_retries=0) as client:
        all_models = sorted({model.id for model in client.models.list()})
    models = all_models
    if settings.enable_tools:
        models = [
            model
            for model in all_models
            if "tools" in ollama_model_capabilities(settings, model)
        ]
    if not models:
        raise ValueError(
            "Keine passenden Ollama-Modelle gefunden. Für aktivierte Tools wird "
            "ein Modell mit Tool-Calling-Unterstützung benötigt."
        )
    print("Verfügbare Ollama-Modelle:")
    for index, model in enumerate(models, start=1):
        print(f"  {index}. {model}")
    while True:
        choice = input("Modellnummer (oder 'exit'): ").strip()
        if choice.lower() in {"exit", "quit"}:
            raise EOFError
        if choice.isascii() and choice.isdecimal() and 1 <= int(choice) <= len(models):
            return replace(settings, model=models[int(choice) - 1])
        print(f"Bitte eine Zahl zwischen 1 und {len(models)} eingeben.")


def main() -> int:
    """Run an interactive conversation until the user exits."""
    args = build_parser().parse_args()

    try:
        settings = Settings.from_env()
        if args.model:
            settings = replace(settings, model=args.model.strip())
        if settings.provider == "ollama" and not settings.model:
            settings = select_ollama_model(settings)
        agent = create_agent(settings)
    except (EOFError, KeyboardInterrupt):
        print("\nChat ended.")
        return 0
    except (OSError, OpenAIError) as error:
        print(
            f"Verbindung fehlgeschlagen: {error}\n"
            "Für Ollama: Ollama starten (gegebenenfalls 'ollama serve') und BASE_URL prüfen.",
            file=sys.stderr,
        )
        return 1
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1

    messages: list[dict[str, str]] = []
    prompt = args.prompt
    print(f"Model: {settings.model}")
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
            try:
                result = agent.invoke({"messages": messages})
            except BadRequestError as error:
                if (
                    settings.provider != "ollama"
                    or "does not support tools" not in str(error).lower()
                ):
                    raise
                raise ValueError(
                    f"{settings.model} unterstützt keine Tools. Bitte ein "
                    "toolfähiges Modell auswählen."
                )
        except (OSError, OpenAIError, ValueError) as error:
            messages.pop()
            print(f"Modellanfrage fehlgeschlagen: {error}", file=sys.stderr)
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
