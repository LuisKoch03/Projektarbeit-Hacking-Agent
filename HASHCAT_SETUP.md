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
HASHCAT_WORDLIST_DIR=wordlists
HASHCAT_WORDLIST=rockyou.txt
```

`HASHCAT_TIMEOUT` begrenzt jeden einzelnen Hashcat-Prozess in Sekunden.
`HASHCAT_WORDLIST_DIR` legt den lokalen Wortlistenordner fest.
`HASHCAT_WORDLIST` legt darin die Standarddatei fuer Woerterbuchangriffe fest.
Alternativ darf `HASHCAT_WORDLIST` weiterhin einen absoluten Dateipfad
enthalten.

## Agent-Tools

Hashcat ist wie Nmap und ZAP im Paket `hacking_agent.tools` registriert. Der
Agent stellt vier Funktionen bereit:

- `hashcat_version` prueft die lokale Installation.
- `identify_hash_folder` bestimmt moegliche Hash-Typen fuer bis zu 50 Dateien.
- `list_hashcat_wordlists` zeigt die direkt im konfigurierten Wortlistenordner
  vorhandenen Dateien an.
- `run_hashcat` startet einen explizit angeforderten Audit. Der Hash kann als
  lokale Datei (`hash_file`) oder direkt (`hash_value`) angegeben werden.
  Wortlisten-Audits verwenden `attack_mode=0` und standardmaessig die mit
  `HASHCAT_WORDLIST` konfigurierte Datei. Mit `wordlist_name` kann das Modell
  eine von `list_hashcat_wordlists` gemeldete Datei innerhalb des Ordners
  auswaehlen. Absolute Pfade und ein Verlassen des Ordners sind gesperrt.
  Begrenzte Masken-/Bruteforce-Audits verwenden `attack_mode=3` und `mask`.

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
oder des direkten Hash-Werts, der Angriffsmethode und des Hash-Modus gestartet
werden.

Direkter Hash mit Wortliste:

```text
Pruefe meinen autorisierten MD5-Hash 098f6bcd4621d373cade4e832627b4f6
mit Hash-Modus 0 und der in HASHCAT_WORDLIST konfigurierten Wortliste.
```

Direkter Hash mit einer begrenzten Ziffernmaske:

```text
Pruefe meinen autorisierten MD5-Hash 81dc9bdb52d04dc20036dbd8313ed055
mit Hash-Modus 0, Angriffsmodus 3 und der Maske ?d?d?d?d.
```

Ein direkt uebergebener Hash wird fuer den Aufruf in einer temporaeren Datei
gespeichert und danach entfernt. So erscheint er nicht als Argument in der
Prozessliste.

## Sicherheit

Hashcat darf nur fuer eigene Hashes oder mit ausdruecklicher Genehmigung
eingesetzt werden. Ergebnisse koennen sensible Kennwoerter enthalten und
sollten nicht in Git, Chat-Protokollen oder anderen gemeinsam genutzten
Dateien gespeichert werden.
