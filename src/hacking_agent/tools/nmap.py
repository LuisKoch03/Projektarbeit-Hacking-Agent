"""Nmap tool for authorized network scans."""

import shutil
import subprocess

from langchain.tools import tool
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = PROJECT_ROOT / "compose.yaml"

@tool
def nmap_scan(
    arguments: list[str],
    timeout_seconds: int = 600,
) -> str:
    """Run Nmap in a temporary Docker container with arbitrary arguments.

    Use only on systems the user owns or is explicitly authorized to scan.
    Supply every token after ``nmap`` as a separate list item; do not include
    the executable itself or shell syntax. Targets are part of the argument
    list, so multiple hosts, CIDR networks, target ranges, and target-related
    options are supported.

    Examples:

    Scan a service running on the Windows host:
    ``["-sT", "-sV", "-p", "3000", "host.docker.internal"]``

    Scan the ZAP service in the same Docker Compose network:
    ``["-sT", "-sV", "-p", "8090", "zap"]``

    Scan an authorized device in the local network:
    ``["-sT", "-sV", "-p", "22,80,443", "192.168.1.10"]``

    Discover authorized hosts in a local subnet:
    ``["-sn", "192.168.1.0/24"]``

    Run an authorized UDP scan:
    ``["-sU", "--top-ports", "20", "--reason", "192.168.1.10"]``

    Run authorized operating-system detection:
    ``["-O", "--osscan-guess", "-T4", "192.168.1.10"]``

    Show the Nmap version:
    ``["--version"]``

    Show the network interfaces inside the Nmap container:
    ``["--iflist"]``

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

    docker = shutil.which("docker")
    if docker is None:
        return "Error: Docker was not found in PATH."

    if not COMPOSE_FILE.is_file():
        return f"Error: Compose file was not found: {COMPOSE_FILE}"

    command = [
        docker,
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "run",
        "--rm",
        "--no-deps",
        "nmap",
        *normalized_arguments,
    ]

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
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
        return f"Error: could not start Docker/Nmap: {error}"

    output = result.stdout.strip()
    if result.stderr.strip():
        output += f"\n{result.stderr.strip()}"
    if result.returncode:
        return f"Error: Nmap exited with code {result.returncode}.\n{output}".strip()
    return output.strip() or "Nmap finished without output."
