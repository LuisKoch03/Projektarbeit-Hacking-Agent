# Projektarbeit Hacking Agent

## Start mit Ollama

1. Ollama installieren und starten. Falls nötig: `ollama serve`.
2. Ein gewünschtes Modell mit `ollama pull <modellname>` herunterladen.
3. Im Projektordner die Abhängigkeiten installieren: `python -m pip install -e .`.
4. Falls noch keine `.env` existiert: `Copy-Item .env.example .env` (PowerShell).
5. `hacking-agent` starten und die Nummer des gewünschten Modells eingeben.

Die `.env` ist für lokales Ollama ohne API-Key vorbereitet und wird von Git ignoriert.
Bei leerem `MODEL` fragt das Programm bei jedem Start nach dem Modell.
Mit `MODEL=<modellname>` in der `.env` oder `hacking-agent --model <modellname>`
lässt sich ein Modell direkt auswählen. Starte das Programm im Projektordner,
damit dessen `.env` geladen wird.

Unterstützt das ausgewählte Ollama-Modell keine Tool-Aufrufe, schaltet das Programm
automatisch auf normalen Chat ohne Projekt-Tools um und wiederholt die Anfrage.
Für den Zugriff auf Projekt-Tools wird ein Modell mit Tool Calling benötigt.
Die Verbindung nutzt Ollamas OpenAI-kompatible Schnittstelle unter `/v1`.

## Nmap als Agent-Tool

Nmap muss installiert und im `PATH` erreichbar sein (`nmap --version`). Nach der
Installation gegebenenfalls das Terminal neu starten. Eine zusätzliche
Python-Bibliothek ist nicht erforderlich.

Das Tool `nmap_scan` ist automatisch beim Agenten registriert. Beispiele im Chat:

> Scanne auf 127.0.0.1 die TCP-Ports 22,80,443 mit Nmap.

> Führe `nmap -sU --top-ports 20 --reason 192.168.1.10` aus.

Das Tool akzeptiert mit `arguments` alle Bestandteile, die in der Kommandozeile
nach `nmap` stehen. Dadurch werden Scan-Typen, mehrere Ziele, CIDR-Netze,
Host-Erkennung, Ports, Dienst- und Betriebssystemerkennung, NSE-Skripte,
Timing-Optionen und Nmap-Ausgabeoptionen unterstützt. Intern wird beispielsweise
`nmap -sV -O -p 1-1000 192.168.1.10` als folgende Argumentliste aufgerufen:

```json
{
  "arguments": ["-sV", "-O", "-p", "1-1000", "192.168.1.10"],
  "timeout_seconds": 600
}
```

Jedes Kommandozeilenargument muss ein eigener Listeneintrag sein. Das Programm
verwendet keine Shell; dadurch werden Zeichen innerhalb eines Arguments nicht
als PowerShell- oder CMD-Befehle ausgeführt. `timeout_seconds` begrenzt die
gesamte Laufzeit auf maximal 3600 Sekunden und ist unabhängig von Nmaps eigener
Option `--host-timeout`. Die Nmap-Ausgabe oder eine Fehlermeldung wird an den
Agenten zurückgegeben. Scanne nur eigene Systeme oder Ziele, für die du eine
Erlaubnis hast.

Für einen externen OpenAI-kompatiblen Dienst: `PROVIDER=openai`, `BASE_URL`,
`API_KEY` und `MODEL` passend in der `.env` setzen.


.\.venv\Scripts\Activate.ps1
