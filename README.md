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

Für einen externen OpenAI-kompatiblen Dienst: `PROVIDER=openai`, `BASE_URL`,
`API_KEY` und `MODEL` passend in der `.env` setzen.
