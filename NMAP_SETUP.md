# Nmap einrichten

## Installation pruefen

Nmap wird derzeit direkt unter Windows ausgefuehrt und nicht aus einem
Container gestartet. Es muss installiert und im `PATH` erreichbar sein:

```powershell
nmap --version
```

Wird der Befehl nicht gefunden, muss Nmap installiert werden. Danach das
Terminal neu starten und den Test wiederholen. Eine zusaetzliche
Python-Bibliothek ist nicht erforderlich.

## Agent-Tool

Das Tool `nmap_scan` ist automatisch beim Agenten registriert. Beispiele fuer
Anfragen im Agenten-Chat:

```text
Scanne auf 127.0.0.1 die TCP-Ports 22, 80 und 443 mit Nmap.
```

```text
Fuehre einen Service-Scan auf Port 3000 von 127.0.0.1 durch.
```

Das Tool akzeptiert mit `arguments` die Bestandteile, die in der Kommandozeile
nach `nmap` stehen. Intern sieht ein Aufruf beispielsweise so aus:

```json
{
  "arguments": ["-sV", "-p", "3000", "127.0.0.1"],
  "timeout_seconds": 600
}
```

Jedes Kommandozeilenargument muss ein eigener Listeneintrag sein. Das Tool
startet Nmap ohne Shell, begrenzt die Laufzeit und gibt die kombinierte
Textausgabe an den Agenten zurueck.

## Sicherheit

Nmap darf nur gegen eigene Systeme oder Ziele eingesetzt werden, fuer die eine
ausdrueckliche Erlaubnis vorliegt.
