"""General tools that can be used by the project agent."""

from langchain.tools import tool

from .hashcat_tools import (
    HASHCAT_TOOLS,
    hashcat_version,
    identify_hash_folder,
    run_hashcat,
)


@tool
def get_project_overview() -> str:
    """Return a short overview of this project."""
    return (
        "This project is a Python framework for a LangChain agent using "
        "OpenAI-compatible API. More tools and project-specific "
        "functionality can be added in hacking_agent/tools.py."
    )


TOOLS = [get_project_overview, *HASHCAT_TOOLS]
