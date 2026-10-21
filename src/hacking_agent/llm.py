"""LangChain agent construction."""

from collections.abc import Sequence

from langchain.agents import create_agent as langchain_create_agent
from langchain_openai import ChatOpenAI

from .config import Settings
from .tools import TOOLS


def create_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create the configured chat model."""
    settings = settings or Settings.from_env()
    return ChatOpenAI(
        api_key=settings.api_key,
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
        tools=list(TOOLS if tools is None else tools),
        system_prompt=settings.system_prompt,
    )
