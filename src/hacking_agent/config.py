"""Application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Settings loaded from environment variables."""

    api_key: str
    base_url: str = "https://api.nano-gpt.com/api/v1"
    model: str = "minimax/minimax-m2.7"
    temperature: float = 0.0
    system_prompt: str = (
        "You are a helpful assistant for the Projektarbeit Hacking Agent. "
        "Be accurate, clear, and explicit about uncertainty."
    )

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from the environment and an optional .env file."""
        load_dotenv()

        api_key = os.getenv("API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "API_KEY is not set. Copy .env.example to .env and add your API key."
            )

        base_url = os.getenv("BASE_URL", cls.base_url).strip() or cls.base_url
        model = os.getenv("ODEL", cls.model).strip() or cls.model
        system_prompt = os.getenv("YSTEM_PROMPT", cls.system_prompt).strip()
        if not system_prompt:
            raise ValueError("YSTEM_PROMPT must not be empty.")
        temperature_text = os.getenv("EMPERATURE", str(cls.temperature))
        try:
            temperature = float(temperature_text)
        except ValueError as error:
            raise ValueError("OPENAI_TEMPERATURE must be a number.") from error

        if not 0 <= temperature <= 2:
            raise ValueError("OPENAI_TEMPERATURE must be between 0 and 2.")

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
