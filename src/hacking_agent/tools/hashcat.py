"""Hashcat tools for authorized local password-auditing workflows."""

import os
from pathlib import Path
import subprocess
import tempfile

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


def _hashcat_wordlist() -> str:
    """Return the optional default wordlist configured for dictionary audits."""
    return os.getenv("HASHCAT_WORDLIST", "").strip()


def _hashcat_wordlist_directory() -> Path:
    """Return the configured directory containing selectable wordlists."""
    configured = os.getenv("HASHCAT_WORDLIST_DIR", "wordlists").strip() or "wordlists"
    return Path(os.path.expandvars(configured)).expanduser().resolve()


def _resolve_hashcat_wordlist(wordlist_name: str | None = None) -> Path:
    """Resolve a configured wordlist or a safe relative name within its directory."""
    directory = _hashcat_wordlist_directory()
    if wordlist_name is not None:
        relative_path = Path(_validated_single_line(wordlist_name, "wordlist_name"))
        if relative_path.is_absolute():
            raise ValueError("wordlist_name must be relative to HASHCAT_WORDLIST_DIR.")
        wordlist_path = (directory / relative_path).resolve()
        if not wordlist_path.is_relative_to(directory):
            raise ValueError("wordlist_name must stay inside HASHCAT_WORDLIST_DIR.")
        return wordlist_path

    configured = _hashcat_wordlist()
    if not configured:
        raise ValueError("Set HASHCAT_WORDLIST in .env.")
    wordlist_path = Path(os.path.expandvars(configured)).expanduser()
    if not wordlist_path.is_absolute():
        wordlist_path = directory / wordlist_path
    return wordlist_path.resolve()


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


def _validated_single_line(value: str, name: str) -> str:
    """Return a non-empty single-line value suitable for a Hashcat argument."""
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string.")
    if not value or any(character in value for character in "\x00\r\n"):
        raise ValueError(f"{name} must be a non-empty single-line string.")
    return value


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
def list_hashcat_wordlists() -> str:
    """List wordlist files available directly in HASHCAT_WORDLIST_DIR."""
    directory = _hashcat_wordlist_directory()
    if not directory.is_dir():
        return f"Error: wordlist directory does not exist: {directory}"
    files = sorted(path for path in directory.iterdir() if path.is_file())
    if not files:
        return f"Error: no wordlist files found in: {directory}"
    return "\n".join(f"{path.name} ({path.stat().st_size} bytes)" for path in files)


@tool
def run_hashcat(
    hash_mode: int,
    hash_file: str | None = None,
    hash_value: str | None = None,
    attack_mode: int = 0,
    mask: str | None = None,
    wordlist_name: str | None = None,
    extra_args: list[str] | None = None,
) -> str:
    """Run an authorized Hashcat dictionary or mask-based password audit.

    Use only for hashes the user owns or is explicitly authorized to audit.
    Provide exactly one of hash_file or hash_value. Attack mode 0 requires a
    local wordlist configured through HASHCAT_WORDLIST. Optionally select a
    listed file by relative wordlist_name within HASHCAT_WORDLIST_DIR; never
    invent or pass an absolute wordlist path. Attack mode 3 performs a
    brute-force/mask audit and requires a mask such as ?d?d?d?d. Supply each
    optional command-line argument as a separate list item.
    """
    if hash_mode < 0 or attack_mode < 0:
        return "Error: hash_mode and attack_mode must be non-negative integers."

    try:
        if (hash_file is None) == (hash_value is None):
            return "Error: provide exactly one of hash_file or hash_value."

        hash_path: Path | None = None
        if hash_file is not None:
            hash_path = Path(_validated_single_line(hash_file, "hash_file")).expanduser()
            if not hash_path.is_file():
                return f"Error: hash file does not exist: {hash_path}"
        else:
            hash_value = _validated_single_line(hash_value, "hash_value")

        candidate_arguments: list[str]
        if attack_mode == 3:
            if wordlist_name is not None:
                return "Error: wordlist_name cannot be used with attack_mode 3."
            if mask is None:
                return "Error: attack_mode 3 requires a mask."
            candidate_arguments = [_validated_single_line(mask, "mask")]
        else:
            if mask is not None:
                return "Error: mask is only supported with attack_mode 3."
            wordlist_path = _resolve_hashcat_wordlist(wordlist_name)
            if not wordlist_path.is_file():
                return f"Error: wordlist does not exist: {wordlist_path}"
            candidate_arguments = [str(wordlist_path)]

        optional_arguments = _validated_extra_args(extra_args)

        def execute(selected_hash_path: Path) -> str:
            result = _run_hashcat(
                [
                    "-m",
                    str(hash_mode),
                    "-a",
                    str(attack_mode),
                    str(selected_hash_path),
                    *candidate_arguments,
                    "--potfile-disable",
                    "--status",
                    *optional_arguments,
                ]
            )
            return _format_result(result)

        if hash_path is not None:
            return execute(hash_path)

        with tempfile.TemporaryDirectory(prefix="hacking-agent-hashcat-") as temp_dir:
            temporary_hash_path = Path(temp_dir) / "hash.txt"
            temporary_hash_path.write_text(f"{hash_value}\n", encoding="utf-8")
            return execute(temporary_hash_path)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return f"Error: unable to run Hashcat: {error}"
