"""Hashcat tools for authorized local password-auditing workflows."""

import os
from pathlib import Path
import subprocess

from langchain.tools import tool


def _hashcat_executable() -> str:
    """Return the configured Hashcat executable."""
    return os.getenv("HASHCAT_PATH", "hashcat").strip() or "hashcat"


def _hashcat_timeout() -> float:
    """Return the validated process timeout configured for Hashcat."""
    timeout = float(os.getenv("HASHCAT_TIMEOUT", "300"))
    if timeout <= 0:
        raise ValueError("HASHCAT_TIMEOUT must be greater than zero.")
    return timeout


def _run_hashcat(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run Hashcat without invoking a shell."""
    return subprocess.run(
        [_hashcat_executable(), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_hashcat_timeout(),
        check=False,
        shell=False,
    )


def _format_result(result: subprocess.CompletedProcess[str]) -> str:
    """Combine Hashcat output and include a non-zero exit code."""
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    if result.returncode:
        return f"Error: Hashcat exited with code {result.returncode}.\n{output}".strip()
    return output or "Hashcat finished without output."


def _validated_extra_args(extra_args: list[str] | None) -> list[str]:
    """Validate optional arguments before passing them directly to Hashcat."""
    normalized: list[str] = []
    for argument in extra_args or []:
        if not isinstance(argument, str):
            raise ValueError("every extra Hashcat argument must be a string.")
        if not argument or any(character in argument for character in "\x00\r\n"):
            raise ValueError(
                "Hashcat arguments must be non-empty single-line strings."
            )
        normalized.append(argument)
    return normalized


@tool
def hashcat_version() -> str:
    """Return the installed Hashcat version."""
    try:
        return _format_result(_run_hashcat(["--version"]))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return f"Error: unable to run Hashcat: {error}"


@tool
def identify_hash_folder(folder: str) -> str:
    """Identify likely hash types in up to 50 files without cracking them."""
    folder_path = Path(folder).expanduser()
    if not folder_path.is_dir():
        return f"Error: hash folder does not exist: {folder_path}"

    files = sorted(path for path in folder_path.iterdir() if path.is_file())[:50]
    if not files:
        return f"Error: no hash files found in: {folder_path}"

    results: list[str] = []
    for path in files:
        try:
            result = _run_hashcat(["--identify", str(path)])
            results.append(f"{path.name}: {_format_result(result)}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            results.append(f"{path.name}: unable to identify ({error})")
    return "\n".join(results)


@tool
def run_hashcat(
    hash_file: str,
    wordlist: str,
    hash_mode: int,
    attack_mode: int = 0,
    extra_args: list[str] | None = None,
) -> str:
    """Run Hashcat for an explicitly selected local hash file and wordlist.

    Use only for hashes the user owns or is explicitly authorized to audit.
    Supply each optional command-line argument as a separate list item.
    """
    hash_path = Path(hash_file).expanduser()
    wordlist_path = Path(wordlist).expanduser()
    if not hash_path.is_file():
        return f"Error: hash file does not exist: {hash_path}"
    if not wordlist_path.is_file():
        return f"Error: wordlist does not exist: {wordlist_path}"
    if hash_mode < 0 or attack_mode < 0:
        return "Error: hash_mode and attack_mode must be non-negative integers."

    try:
        optional_arguments = _validated_extra_args(extra_args)
        result = _run_hashcat(
            [
                "-m",
                str(hash_mode),
                "-a",
                str(attack_mode),
                str(hash_path),
                str(wordlist_path),
                "--potfile-disable",
                "--status",
                *optional_arguments,
            ]
        )
        return _format_result(result)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return f"Error: unable to run Hashcat: {error}"
