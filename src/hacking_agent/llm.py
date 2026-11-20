"""LangChain agent construction."""

from collections.abc import Sequence
import json
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from langchain.agents import create_agent as langchain_create_agent
from langchain_openai import ChatOpenAI

from .config import Settings
from .tools import TOOLS


def ollama_model_capabilities(
    settings: Settings,
    model: str,
    timeout: float = 5,
) -> set[str]:
    """Return capabilities reported by Ollama's native model endpoint.

    Ollama's OpenAI-compatible ``/v1/models`` endpoint does not expose whether
    a model supports tools. The native ``/api/show`` endpoint does, so the UI
    can avoid silently selecting a text-only model for an agent with tools.
    """
    parsed_url = urlsplit(settings.base_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("BASE_URL must be an absolute URL.")

    show_url = urlunsplit(
        (parsed_url.scheme, parsed_url.netloc, "/api/show", "", "")
    )
    request = Request(
        show_url,
        data=json.dumps({"model": model}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list):
        return set()
    return {item for item in capabilities if isinstance(item, str)}


def create_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create the configured chat model."""
    settings = settings or Settings.from_env()
    if not settings.model:
        raise ValueError("Select a model in the CLI or set MODEL in .env.")
    return ChatOpenAI(
        api_key="ollama" if settings.provider == "ollama" else settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        temperature=settings.temperature,
    )


def create_agent(
    settings: Settings | None = None,
    tools: Sequence[object] | None = None,
):
    """Create a LangChain agent with the configured model and instructions."""
    settings = settings or Settings.from_env()
    return langchain_create_agent(
        model=create_model(settings),
        tools=list(TOOLS if settings.enable_tools and tools is None else tools or []),
        system_prompt=settings.system_prompt,
    )
