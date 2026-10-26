"""Tools that can be used by the project agent."""

import shutil
import subprocess

from langchain.tools import tool


@tool
def get_project_overview() -> str:
    """Return a short overview of this project."""
    return (
        "This project is a Python framework for a LangChain agent using "
        "OpenAI-compatible API. More tools and project-specific "
        "functionality can be added in hacking_agent/tools.py."
    )


@tool
def nmap_scan(
    arguments: list[str],
    timeout_seconds: int = 600,
) -> str:
    """Run locally installed Nmap with arbitrary command-line arguments.

    Use only on systems the user owns or is explicitly authorized to scan.
    Supply every token after ``nmap`` as a separate list item; do not include
    the executable itself or shell syntax. Targets are part of the argument
    list, so multiple hosts, CIDR networks, target ranges, and target-related
    options are supported.

    Examples:
    ``["-sT", "-sV", "-p", "22,80,443", "192.168.1.10"]``
    ``["-sn", "192.168.1.0/24"]``
    ``["-sU", "--top-ports", "20", "--reason", "host.example"]``
    ``["-O", "--osscan-guess", "-T4", "10.0.0.5"]``
    ``["-V"]`` or ``["--iflist"]``

    Nmap options that need a value must use a separate list item unless Nmap
    documents an equals form. For example use ``["-p", "1-1000", TARGET]``.
    ``timeout_seconds`` is the wrapper's process timeout (1 to 3600 seconds),
    independent of Nmap's own ``--host-timeout`` option. The tool returns
    Nmap's combined text output.
    """
    if not arguments:
        return "Error: arguments must contain at least one Nmap option or target."
    if not 1 <= timeout_seconds <= 3600:
        return "Error: timeout_seconds must be between 1 and 3600."

    normalized_arguments: list[str] = []
    for argument in arguments:
        if not isinstance(argument, str):
            return "Error: every Nmap argument must be a string."
        if not argument or "\x00" in argument or "\r" in argument or "\n" in argument:
            return "Error: Nmap arguments must be non-empty single-line strings."
        normalized_arguments.append(argument)

    executable = shutil.which("nmap")
    if executable is None:
        return "Error: Nmap was not found in PATH. Install Nmap and restart the terminal."

    # A list plus shell=False passes arguments to Nmap verbatim instead of
    # interpreting them as PowerShell or cmd commands.
    command = [executable, *normalized_arguments]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return f"Error: Nmap scan exceeded {timeout_seconds} seconds and was stopped."
    except OSError as error:
        return f"Error: could not start Nmap: {error}"

    output = result.stdout.strip()
    if result.stderr.strip():
        output += f"\n{result.stderr.strip()}"
    if result.returncode:
        return f"Error: Nmap exited with code {result.returncode}.\n{output}".strip()
    return output.strip() or "Nmap finished without output."


TOOLS = [get_project_overview, nmap_scan]
