# Langdock-Agent „Mein Tag“: Tagesbriefing aus Outlook

Ein Knopfdruck ergibt: Termine heute, wichtige Mails nach Priorität, To-do-Liste und einen Vorschlag für die 3 wichtigsten Aufgaben.

## 1. Grunddaten
| Feld | Eintrag |
|---|---|
| Name | Mein Tag |
| Beschreibung | Tägliches Briefing aus Outlook-Mails und -Kalender mit Priorisierung und To-do-Verwaltung. |
| Icon | ☀️ |
| Anweisungen | kompletter Inhalt von `01_anweisungen.md` |

## 2. Modell
**Empfehlung: Claude Sonnet (neueste Version im Workspace).** Das Briefing läuft täglich, ruft viele Mails und Termine über die Integration ab und soll in Sekunden fertig sein. Sonnet ist dafür schnell, zuverlässig bei Tool-Aufrufen und gut im Priorisieren und Zusammenfassen.
Alternative: **Claude Opus**, wenn du sehr viele lange, verschachtelte Threads hast und die Priorisierung besonders fein sein soll. Es ist langsamer.
Kreativität: **niedrig** (≤ 0,2).

## 3. Integrationen / Aktionen
Unter „Aktionen“ die **Outlook**-Integration hinzufügen und mindestens aktivieren:
- E-Mails suchen/auflisten und E-Mail lesen
- Kalendertermine auflisten
- optional: Entwurf erstellen, Termin erstellen, Aufgaben/To Do (falls in eurem Langdock angeboten)

Bei schreibenden Aktionen (Senden, Termin anlegen) die Bestätigung durch den Nutzer aktiviert lassen, falls Langdock das anbietet. Die Anweisungen verlangen sie zusätzlich.
Fähigkeiten: Websuche **aus** (nicht nötig, hält das Briefing schlank), Datenanalyse optional, Canvas optional.

## 4. Wissen
`02_prioritaeten-profil.md` ausfüllen (wichtige Personen, Themen, Delegation, ignorierbare Absender) und hochladen. Das ist der größte Hebel für eine gute Priorisierung.

## 5. Konversationsstarter (= dein Knopf)
- ☀️ Mein Tag
- 📆 Wochenblick
- ✅ Meine To-dos
- ✍️ Antwortentwürfe für alle 🔴-Mails

## 6. Täglich automatisch (optional)
Falls euer Langdock-Workspace Workflows mit Zeitplan-Auslöser hat, kannst du das Briefing werktags z. B. um 7:30 laufen lassen und dir per Mail an dich selbst schicken. Prompt: „Erstelle mein Tagesbriefing“, dazu den Agenten „Mein Tag“ und die Aktion „E-Mail senden“ an die eigene Adresse. Sonst gilt: morgens den Agenten öffnen und auf „☀️ Mein Tag“ klicken.

## 7. To-dos
- Bietet die Integration Aufgaben/To-Do-Aktionen an, verwaltet der Agent die Liste direkt in Microsoft To Do / Outlook.
- Sonst führt er die Liste im Chat und gibt am Ende einen „To-do-Stand“-Block aus. Für ein durchgehendes Gedächtnis den Chat über die Woche weiterführen oder den Block morgens einfügen.
- Befehle: „Erledigt: …“, „Neu: … bis Freitag“, „Verschieben: … auf Montag“, „wartet auf Anna“.
