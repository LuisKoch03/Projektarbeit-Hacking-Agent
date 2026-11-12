# Hashcat einrichten

## Installation pruefen

Hashcat wird direkt unter Windows ausgefuehrt und muss installiert sein. Ist
die ausfuehrbare Datei im `PATH` erreichbar, kann die Installation so geprueft
werden:

```powershell
hashcat --version
```

Andernfalls wird der vollstaendige Pfad in `.env` eingetragen:

```env
HASHCAT_PATH=C:\Pfad\zu\hashcat.exe
HASHCAT_TIMEOUT=300
```

`HASHCAT_TIMEOUT` begrenzt jeden einzelnen Hashcat-Prozess in Sekunden.

## Agent-Tools

Hashcat ist wie Nmap und ZAP im Paket `hacking_agent.tools` registriert. Der
Agent stellt drei Funktionen bereit:

- `hashcat_version` prueft die lokale Installation.
- `identify_hash_folder` bestimmt moegliche Hash-Typen fuer bis zu 50 Dateien.
- `run_hashcat` startet einen explizit angeforderten Audit mit einer lokalen
  Hash-Datei, einer Wortliste und dem angegebenen Hash-Modus.

Optionale Hashcat-Argumente werden als Liste einzelner Argumente uebergeben.
Hashcat wird ohne Shell gestartet. Die Potfile wird fuer Agent-Aufrufe
deaktiviert, damit keine geknackten Kennwoerter dauerhaft gespeichert werden.

## Beispielanfragen

```text
Pruefe, ob Hashcat installiert ist, und zeige mir die Version.
```

```text
Identifiziere die Hash-Typen der Dateien in C:\Audit\Hashes.
```

Ein Passwort-Audit darf erst nach einer ausdruecklichen Auswahl der Hash-Datei,
der Wortliste und des Hash-Modus gestartet werden.

## Sicherheit

Hashcat darf nur fuer eigene Hashes oder mit ausdruecklicher Genehmigung
eingesetzt werden. Ergebnisse koennen sensible Kennwoerter enthalten und
sollten nicht in Git, Chat-Protokollen oder anderen gemeinsam genutzten
Dateien gespeichert werden.
