"""Hashcat tools for authorized local password-auditing workflows."""

import os
import subprocess
from pathlib import Path

from langchain.tools import tool


def _hashcat_executable() -> str:
    """Return the configured hashcat executable."""
    return os.getenv("HASHCAT_PATH", "hashcat").strip() or "hashcat"


def _run_hashcat(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run hashcat without invoking a shell."""
    timeout = float(os.getenv("HASHCAT_TIMEOUT", "300"))
    if timeout <= 0:
        raise ValueError("HASHCAT_TIMEOUT must be greater than zero.")

    return subprocess.run(
        [_hashcat_executable(), *arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


@tool
def hashcat_version() -> str:
    """Return the installed hashcat version."""
    try:
        result = _run_hashcat(["--version"])
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return f"Unable to run hashcat: {error}"

    output = (result.stdout or result.stderr).strip()
    return output or f"hashcat exited with code {result.returncode}"


@tool
def identify_hash_folder(folder: str) -> str:
    """Identify likely hash types for files in a local folder.

    This performs discovery only. It does not attempt to crack any hashes.
    At most 50 regular files are inspected per call.
    """
    folder_path = Path(folder).expanduser()
    if not folder_path.is_dir():
        return f"Hash folder does not exist: {folder_path}"

    files = sorted(path for path in folder_path.iterdir() if path.is_file())[:50]
    if not files:
        return f"No hash files found in: {folder_path}"

    results: list[str] = []
    for path in files:
        try:
            result = _run_hashcat(["--identify", str(path)])
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            results.append(f"{path.name}: unable to identify ({error})")
            continue

        output = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        results.append(f"{path.name}: {output or f'exited with code {result.returncode}'}")

    return "\n".join(results)


@tool
def run_hashcat(
    hash_file: str,
    wordlist: str,
    hash_mode: int,
    attack_mode: int = 0,
    extra_args: str = "",
) -> str:
    """Run hashcat against a local hash file and wordlist.

    The caller must provide paths to files that already exist. Extra hashcat
    options are passed as whitespace-separated arguments and are never run
    through a shell.
    """
    hash_path = Path(hash_file).expanduser()
    wordlist_path = Path(wordlist).expanduser()
    if not hash_path.is_file():
        return f"Hash file does not exist: {hash_path}"
    if not wordlist_path.is_file():
        return f"Wordlist does not exist: {wordlist_path}"
    if hash_mode < 0 or attack_mode < 0:
        return "hash_mode and attack_mode must be non-negative integers."

    arguments = [
        "-m",
        str(hash_mode),
        "-a",
        str(attack_mode),
        str(hash_path),
        str(wordlist_path),
        "--potfile-disable",
        "--status",
    ]
    if extra_args.strip():
        arguments.extend(extra_args.split())

    try:
        result = _run_hashcat(arguments)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return f"Unable to run hashcat: {error}"

    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    return output or f"hashcat exited with code {result.returncode}"


HASHCAT_TOOLS = [hashcat_version, identify_hash_folder, run_hashcat]