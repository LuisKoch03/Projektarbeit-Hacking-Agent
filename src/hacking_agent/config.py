"""Application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Settings loaded from environment variables."""

    api_key: str = ""
    base_url: str = "http://localhost:11434/v1"
    model: str = ""
    provider: str = "ollama"
    temperature: float = 0.0
    system_prompt: str = (
        "You are a helpful assistant for the Projektarbeit Hacking Agent. "
        "Be accurate, clear, and explicit about uncertainty."
    )

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from the environment and an optional .env file."""
        load_dotenv()

        provider = os.getenv("PROVIDER", cls.provider).strip().lower()
        if provider not in {"ollama", "openai"}:
            raise ValueError("PROVIDER must be 'ollama' or 'openai'.")
        api_key = os.getenv("API_KEY", "").strip()
        if provider == "openai" and not api_key:
            raise ValueError(
                "API_KEY is not set. Copy .env.example to .env and add your API key."
            )

        default_url = cls.base_url if provider == "ollama" else "https://api.nano-gpt.com/api/v1"
        base_url = os.getenv("BASE_URL", default_url).strip() or default_url
        model = os.getenv("MODEL", cls.model).strip() or cls.model
        if provider == "openai" and not model:
            raise ValueError("MODEL must be set for PROVIDER=openai.")
        system_prompt = os.getenv("SYSTEM_PROMPT", cls.system_prompt).strip()
        if not system_prompt:
            raise ValueError("SYSTEM_PROMPT must not be empty.")
        temperature_text = os.getenv("TEMPERATURE", str(cls.temperature))
        try:
            temperature = float(temperature_text)
        except ValueError as error:
            raise ValueError("TEMPERATURE must be a number.") from error

        if not 0 <= temperature <= 2:
            raise ValueError("TEMPERATURE must be between 0 and 2.")

        return cls(
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
