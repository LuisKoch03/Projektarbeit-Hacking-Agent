# OWASP ZAP mit Docker starten

## Was eingerichtet wurde

ZAP wird nicht als Windows-Programm installiert. Die Datei `compose.yaml`
startet stattdessen das offizielle stabile ZAP-Image als separaten Container.
Die ZAP-API ist nur lokal unter `127.0.0.1:8090` erreichbar und wird durch den
API-Schluessel aus `.env` geschuetzt.

`ZAP_PORT` ist ebenfalls auf `8090` gesetzt, damit der eingebaute
Container-Healthcheck denselben Port wie der ZAP-Dienst kontrolliert.

Die lokale `.env` wird von Git ignoriert. In `.env.example` steht deshalb nur
ein Platzhalter und kein verwendbarer Schluessel.

## Voraussetzungen

- Docker Desktop ist gestartet.
- PowerShell befindet sich im Projektordner:

  ```powershell
  cd D:\Projektarbeit\Projektarbeit-Hacking-Agent
  ```

## ZAP erstmals starten

```powershell
docker compose up -d zap
```

Beim ersten Start laedt Docker das ZAP-Image herunter. Danach kann ZAP einige
Sekunden benoetigen, bis die API bereit ist.

## Status kontrollieren

```powershell
docker compose ps
docker compose logs zap
```

In `docker compose ps` sollte der ZAP-Service den Status `Up` haben und die
Portzuordnung `127.0.0.1:8090->8090/tcp` anzeigen.

## API testen

Der folgende PowerShell-Code liest den Schluessel aus `.env`, ohne dass er in
den Befehl kopiert werden muss:

```powershell
$zapKeyLine = Get-Content .env | Where-Object { $_ -match '^ZAP_API_KEY=' } | Select-Object -Last 1
$zapKey = $zapKeyLine.Substring('ZAP_API_KEY='.Length)
Invoke-RestMethod "http://127.0.0.1:8090/JSON/core/view/version/?apikey=$zapKey"
```

Bei Erfolg antwortet ZAP mit seiner Versionsnummer.

## ZAP stoppen und erneut starten

Stoppen, ohne den Container zu entfernen:

```powershell
docker compose stop zap
```

Erneut starten:

```powershell
docker compose start zap
```

Container entfernen:

```powershell
docker compose down
```

Das heruntergeladene ZAP-Image bleibt dabei erhalten.

## Naechster Entwicklungsschritt

Das Agent-Tool `zap_scan` ist in `src/hacking_agent/tools.py` registriert. Es
nutzt den laufenden Container ueber `ZAP_BASE_URL` und akzeptiert nur Hosts aus
`ZAP_ALLOWED_HOSTS`.

Beispiel fuer einen passiven Scan im Agenten-Chat:

```text
Fuehre einen passiven ZAP-Scan gegen http://host.docker.internal:3000 aus.
```

Ein aktiver Scan muss im Chat ausdruecklich verlangt werden. Das Tool verlangt
zusaetzlich `authorization_confirmed=true`. Aktive Scans duerfen nur gegen
eigene oder ausdruecklich autorisierte Ziele ausgefuehrt werden.
