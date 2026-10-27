# Ollama einrichten

## Voraussetzungen

- Python 3.10 oder neuer
- Ollama
- ein Ollama-Modell mit Tool-Calling-Unterstuetzung

## Ollama starten

Ollama laeuft unter Windows normalerweise im Hintergrund. Falls der Dienst
nicht erreichbar ist, kann er manuell gestartet werden:

```powershell
ollama serve
```

## Modell herunterladen

```powershell
ollama pull <modellname>
```

Die lokal vorhandenen Modelle lassen sich so anzeigen:

```powershell
ollama list
```

## Python-Umgebung vorbereiten

Im Projektordner:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Falls noch keine lokale Konfiguration existiert:

```powershell
Copy-Item .env.example .env
```

Die Standardkonfiguration fuer Ollama lautet:

```env
PROVIDER=ollama
BASE_URL=http://localhost:11434/v1
API_KEY=
MODEL=
TEMPERATURE=0.0
```

Bei leerem `MODEL` fragt das Programm beim Start nach einem der installierten
Modelle. Ein Modell kann alternativ fest in `.env` oder beim Start angegeben
werden:

```powershell
hacking-agent --model <modellname>
```

## Agent starten

```powershell
hacking-agent
```

Unterstuetzt das gewaehlte Modell keine Tool-Aufrufe, schaltet das Programm auf
normalen Chat ohne Projekt-Tools um. Fuer Nmap und ZAP ist deshalb ein Modell
mit Tool Calling erforderlich.

## Externer OpenAI-kompatibler Dienst

Fuer einen externen Dienst werden diese Werte in `.env` angepasst:

```env
PROVIDER=openai
BASE_URL=https://example.invalid/v1
API_KEY=change-me
MODEL=change-me
```

Die `.env` wird von Git ignoriert und darf echte Zugangsdaten enthalten. Die
`.env.example` enthaelt dagegen nur eine Vorlage.
