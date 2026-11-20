"""Tests for model capability discovery."""

from io import BytesIO
import json
import unittest
from unittest.mock import patch

from hacking_agent.config import Settings
from hacking_agent.llm import ollama_model_capabilities


class _Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class OllamaCapabilitiesTests(unittest.TestCase):
    def test_reads_tools_capability_from_native_ollama_endpoint(self) -> None:
        settings = Settings(
            base_url="http://localhost:11434/v1",
            model="example",
        )
        response = _Response(
            json.dumps({"capabilities": ["completion", "tools"]}).encode()
        )

        with patch("hacking_agent.llm.urlopen", return_value=response) as mocked:
            capabilities = ollama_model_capabilities(settings, "example")

        self.assertEqual(capabilities, {"completion", "tools"})
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/show")
        self.assertEqual(json.loads(request.data), {"model": "example"})

    def test_ignores_invalid_capability_values(self) -> None:
        settings = Settings(base_url="http://localhost:11434/v1")
        response = _Response(
            json.dumps({"capabilities": ["completion", 123, None]}).encode()
        )

        with patch("hacking_agent.llm.urlopen", return_value=response):
            capabilities = ollama_model_capabilities(settings, "example")

        self.assertEqual(capabilities, {"completion"})


if __name__ == "__main__":
    unittest.main()
