"""Core package for the project work agent."""

from .config import Settings
from .llm import create_model

__all__ = ["Settings", "create_model"]
