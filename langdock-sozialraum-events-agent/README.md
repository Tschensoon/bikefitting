# Langdock-Agent „Sozialraum-Scout“: Veranstaltungen für Fröbel-Kitas

Findet Feste und Veranstaltungen im Umkreis einer Kita (Standard 10 km), bewertet, ob sich eine Teilnahme lohnt, und schlägt ein passendes Kinder-Mitmachprogramm vor. Auf Wunsch entwirft er die Anfrage an den Veranstalter, eine Checkliste und einen Jahresplan mit Anmeldefristen. Funktioniert für jede Region in Deutschland.

## 1. Grunddaten
| Feld | Eintrag |
|---|---|
| Name | Sozialraum-Scout |
| Beschreibung | Findet und bewertet Feste und Veranstaltungen im Umfeld einer Fröbel-Kita und schlägt passende Mitmachangebote vor. |
| Icon | 🎪 |
| Anweisungen | kompletter Inhalt von `01_anweisungen.md` |

## 2. Modell
**Empfehlung: Claude Opus (neueste Version im Workspace).** Die Aufgabe braucht viele Websuchen über verstreute lokale Quellen (Gemeindekalender, Vereine, Kirchengemeinden), saubere Prüfung und eine abgewogene Bewertung. Opus ist dabei am gründlichsten und erfindet am seltensten Termine.
Alternative für schnelle Abfragen („Was ist im Dezember los?“): **Claude Sonnet**.
Kreativität: **niedrig bis mittel** (ca. 0,3). Die Recherche soll genau sein, die Ideen für Mitmachprogramme dürfen etwas freier sein.

## 3. Fähigkeiten / Aktionen
| Fähigkeit | Einstellung |
|---|---|
| Websuche | **an (Pflicht)** |
| Datenanalyse | an (Luftlinie, CSV-Export) |
| Canvas | optional (Anfrage-Mails, Checklisten bearbeiten) |
| Outlook (Aktion) | optional: Termine/Fristen in den Kalender eintragen, Entwurf an Veranstalter speichern (nur nach Bestätigung) |
| Route berechnen | optional, dieselbe Integration wie beim Kita-Radar (OSM/OSRM) |

## 4. Wissen (hochladen)
1. `02_skill_sozialraum-event-recherche.md`: Quellen, Suchbegriffe, Bewertungsraster
2. `04_mitmach-baukasten.md`: Ideen für Mitmachprogramme (gern um eure bewährten Angebote ergänzen)
3. `03_kita-profil_vorlage.md`: ausgefüllt pro Kita (Adresse, Personal, Budget, Material, Schwerpunkte). So muss der Agent weniger nachfragen und die Vorschläge passen besser.
4. Optional: `froebel-standorte.csv` aus dem Kita-Radar-Agenten

## 5. Konversationsstarter
- 🎪 Veranstaltungen für meine Kita finden (10 km, nächste 6 Monate)
- 📅 Jahresplan mit Anmeldefristen für meine Kita
- 👩‍🏫 Job- und Ausbildungsmessen in der Region (Fachkräftegewinnung)
- ✉️ Anfrage an Veranstalter entwerfen
- 🧩 Mitmachprogramm für ein Fest ausarbeiten

## 6. So läuft's
1. Agent fragt Kita, Radius, Zeitraum, Ziel (Sichtbarkeit / Vernetzung / Fachkräfte / Image) und Kapazität ab. Mit „Standard“ startet er sofort.
2. Ergebnis:
   - Sozialraum-Kurzprofil und geprüfte Quellen
   - Empfehlungstabelle mit Punktwert und Kategorie (⭐ Top / 👍 Prüfen / 🤝 Vernetzen), Entfernung, Kosten, Anmeldefrist und Mitmach-Vorschlag
   - Fristen-Ampel und Jahresplan für wiederkehrende Feste
3. Danach z. B.:
   - „Anfrage für #2 entwerfen“
   - „Mitmachprogramm für #1 ausarbeiten“
   - „Checkliste Standplanung“
   - „Export“

## 7. Tipp
Den Jahresplan einmal im Herbst für das Folgejahr erstellen lassen. Viele Stadtteilfeste vergeben die Stände schon im Winter oder Frühjahr.
