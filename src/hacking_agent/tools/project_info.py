"""Project-information tool."""

from langchain.tools import tool


@tool
def get_project_overview() -> str:
    """Return a short overview of this project."""
    return (
        "This project is a Python framework for a LangChain agent using "
        "OpenAI-compatible API. More tools and project-specific "
        "functionality can be added in hacking_agent/tools/."
    )
