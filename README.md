# Projektarbeit Hacking Agent

Der Projektarbeit Hacking Agent ist ein modularer Python-Agent fuer
autorisierte Sicherheitsanalysen. Er basiert auf LangChain und verwendet ein
OpenAI-kompatibles Sprachmodell. Standardmaessig wird ein lokal ausgefuehrtes
Ollama-Modell eingesetzt.

Der Agent verbindet die dialogbasierte Planung eines Sprachmodells mit
konkret begrenzten Sicherheitstools. Nmap untersucht Hosts, Ports und Dienste.
OWASP ZAP untersucht Webanwendungen mit Spider-, Passive- und optionalen
Active-Scans. Hashcat identifiziert Hash-Typen und fuehrt explizit angeforderte
Passwort-Audits mit Hash-Dateien oder direkt angegebenen Hashes sowie mit
Wortlisten oder begrenzten Bruteforce-Masken aus. ZAP wird
reproduzierbar als Docker-Service bereitgestellt, waehrend Nmap und Hashcat
derzeit direkt auf dem Windows-System ausgefuehrt werden.

Sicherheitsfunktionen duerfen ausschliesslich gegen eigene Systeme oder Ziele
verwendet werden, fuer die eine ausdrueckliche Genehmigung vorliegt. Aktive
ZAP-Scans erfordern sowohl eine ausdrueckliche Bestaetigung als auch einen
Eintrag des Zielhosts in der lokalen Allowlist.

Die Einrichtung und Bedienung sind in separaten Dokumenten beschrieben:

- [Ollama einrichten](OLLAMA_SETUP.md)
- [Nmap einrichten](NMAP_SETUP.md)
- [OWASP ZAP einrichten](ZAP_SETUP.md)
- [Hashcat einrichten](HASHCAT_SETUP.md)
- [Wichtige Befehle](COMMANDS.md)
