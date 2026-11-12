"""Tools exposed to the LangChain agent."""

from .hashcat import hashcat_version, identify_hash_folder, run_hashcat
from .nmap import nmap_scan
from .project_info import get_project_overview
from .zap import zap_scan

TOOLS = [
    get_project_overview,
    nmap_scan,
    zap_scan,
    hashcat_version,
    identify_hash_folder,
    run_hashcat,
]

__all__ = [
    "TOOLS",
    "get_project_overview",
    "hashcat_version",
    "identify_hash_folder",
    "nmap_scan",
    "run_hashcat",
    "zap_scan",
]
