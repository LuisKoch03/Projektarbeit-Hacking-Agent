# Projektarbeit Hacking Agent

## Setup

Create a virtual environment and install the project:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Copy `.env.example` to `.env` and set `API_KEY`. Install [hashcat](https://hashcat.net/hashcat/)
separately, then set `HASHCAT_PATH` to its executable if it is not available on `PATH`.
The configured model must support tool calls when `ENABLE_TOOLS=true` (the default).
For a model that only supports chat, set `ENABLE_TOOLS=false`; hashcat tools will then
be unavailable until a tool-capable model is selected.

## Hashcat tools

The agent exposes `hashcat_version`, `identify_hash_folder`, and `run_hashcat`.
`identify_hash_folder` scans up to 50 local files and asks hashcat to identify their
likely types without cracking them. `run_hashcat` accepts a selected local hash file,
wordlist, hash mode, attack mode, and optional whitespace-separated hashcat arguments.
It invokes hashcat without a shell and stops after `HASHCAT_TIMEOUT` seconds.

Cracking is intentionally an explicit operation for a selected file and wordlist;
the agent does not automatically crack every file it discovers.

Only use these tools on hashes and systems you are authorized to test.