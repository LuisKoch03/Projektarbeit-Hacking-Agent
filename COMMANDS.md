# Wichtige Befehle

Alle Befehle werden, sofern nicht anders angegeben, im Projektordner
`D:\Projektarbeit\Projektarbeit-Hacking-Agent` ausgefuehrt.

## Python-Umgebung

Virtuelle Umgebung erstellen:

```powershell
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Projekt und Abhaengigkeiten installieren:

```powershell
python -m pip install -e .
```

Virtuelle Umgebung verlassen:

```powershell
deactivate
```

## Agent

Interaktiv starten:

```powershell
hacking-agent
```

Mit festem Modell starten:

```powershell
hacking-agent --model <modellname>
```

Eine erste Anfrage direkt uebergeben:

```powershell
hacking-agent "Pruefe mit Nmap den Port 3000 auf 127.0.0.1."
```

## Ollama

Dienst manuell starten:

```powershell
ollama serve
```

Modelle anzeigen:

```powershell
ollama list
```

Modell herunterladen:

```powershell
ollama pull <modellname>
```

## Docker und ZAP

ZAP starten oder aktualisierte Konfiguration anwenden:

```powershell
docker compose up -d zap
```

Status anzeigen:

```powershell
docker compose ps
```

ZAP-Protokoll anzeigen:

```powershell
docker compose logs zap
```

ZAP stoppen:

```powershell
docker compose stop zap
```

ZAP-Container entfernen:

```powershell
docker compose down
```

## Juice Shop

Juice Shop erstmalig erstellen und starten:

```powershell
docker run -d --name juice-shop -p 127.0.0.1:3000:3000 bkimminich/juice-shop
```

Vorhandenen Juice Shop starten:

```powershell
docker start juice-shop
```

Juice Shop stoppen:

```powershell
docker stop juice-shop
```

Laufende Container anzeigen:

```powershell
docker ps
```

## Nmap

Installation pruefen:

```powershell
nmap --version
```

Juice-Shop-Port direkt pruefen:

```powershell
nmap -sV -p 3000 127.0.0.1
```

## Beispielanfragen an den Agenten

Passiver ZAP-Scan:

```text
Der lokale Juice Shop ist mein autorisiertes Testziel. Fuehre einen passiven
ZAP-Scan gegen http://host.docker.internal:3000 aus.
```

Nmap und ZAP kombinieren:

```text
Der lokale Juice Shop ist mein autorisiertes Testziel. Pruefe zuerst mit Nmap
den Port 3000 auf 127.0.0.1. Fuehre danach einen passiven ZAP-Scan gegen
http://host.docker.internal:3000 aus und fasse beide Ergebnisse zusammen.
```
