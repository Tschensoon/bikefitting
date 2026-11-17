# Feste-Finder für Copilot: Anleitung in 5 Minuten

Damit finden Kitaleitungen Feste in der Nähe ihrer Kita, bei denen die Kita mitmachen kann. Sie schreiben nur die Adresse der Kita und bekommen eine kurze Liste mit Ideen.

## Agent anlegen (einmalig, z. B. durch Region oder IT)
1. Microsoft 365 Copilot öffnen, links **„Agent erstellen“** (oder „Neuer Agent“) wählen. Dann oben auf **„Konfigurieren“** klicken.
2. Felder ausfüllen:

**Name:**
```
Feste-Finder
```

**Beschreibung:**
```
Findet Feste in der Nähe deiner Kita, bei denen ihr mit einem Mitmachangebot für Kinder dabei sein könnt.
```

**Anweisungen:** den kompletten Text aus `anweisungen.txt` hineinkopieren.

3. **Wissen:** Den Schalter **„Websuche“** bzw. **„Im Web suchen“** einschalten. Das ist wichtig, ohne Websuche findet der Agent nichts. Sonst nichts hochladen.

3b. **Code-Interpreter einschalten** (für den Excel-Download): unter „Skills“ bzw. „Funktionen“ → „Hinzufügen“ → **Code-Interpreter**. Ohne ihn kann der Agent keine Excel-Datei erstellen.

4. **Eingabeaufforderungen / Starter** (je Titel + Text):
| Titel | Text |
|---|---|
| Feste suchen | Finde Feste in der Nähe meiner Kita. |
| Schnell: 7 km, 3 Monate | Finde Feste bis 7 km um meine Kita für die nächsten 3 Monate. |
| Jahresplanung | Finde Feste bis 7 km um meine Kita für das ganze Jahr. |
| Anfrage-Mail | Schreib mir eine Anfrage-Mail an einen Veranstalter. |

5. **Modell:** Wenn eine Auswahl angezeigt wird, das stärkste Modell für Recherche bzw. „Reasoning“ wählen. Gibt es keine Auswahl (üblich in Microsoft 365 Copilot), einfach so lassen.

6. Rechts im Testfenster ausprobieren, z. B. mit `Unsere Kita: Musterstraße 1, 20095 Hamburg`. Danach **„Erstellen“** klicken und über **„Teilen“** für die Kitaleitungen freigeben.

## Kurzanleitung für Kitaleitungen (zum Weitergeben)

> **So nutzt du den Feste-Finder**
> 1. In Copilot links auf **„Feste-Finder“** klicken.
> 2. Auf **„Feste suchen“** klicken.
> 3. Den Namen oder die Adresse deiner Kita eintippen.
> 4. Der Agent fragt dann zwei Dinge. Antworte jeweils nur mit einer Zahl:
>    - Wie weit? 1 = bis 5 km, 2 = bis 7 km, 3 = bis 10 km, 4 = anderer Umkreis
>    - Wann? 1 = nächste 4 Wochen, 2 = nächste 3 Monate, 3 = nächste 6 Monate, 4 = ganzes Jahr
>
> Schneller geht es mit allem in einer Nachricht, z. B.: **Kita Sonnenschein, 2, 3**
>
> Du bekommst bis zu 10 Feste mit Datum, Ort, einer Idee zum Mitmachen und dem Kontakt.
> Danach wieder mit einer Zahl antworten: 1 = Anfrage-Mail, 2 = Idee genauer, 3 = weitersuchen, 4 = neue Suche, **5 = als Excel-Datei herunterladen**.
>
> Bitte vor der Anmeldung immer kurz auf der Seite des Veranstalters prüfen, ob alles stimmt.

## Echte Klick-Knöpfe (optional, mit Copilot Studio)
Im normalen „Agent erstellen“ von Microsoft 365 Copilot gibt es nur die Starter-Knöpfe am Anfang. Mitten im Gespräch kann man dort keine Knöpfe festlegen, deshalb antwortet man mit Zahlen.
Echte Knöpfe für Umkreis und Zeitraum gehen mit **Copilot Studio** (braucht eine Lizenz bzw. Freigabe durch die IT). Grober Ablauf, die Menünamen können leicht abweichen:
1. Agent in Copilot Studio anlegen, Name, Beschreibung und `anweisungen.txt` wie oben eintragen. Unter Wissen die Websuche aktivieren.
2. Neues **Thema** „Feste suchen“ mit Auslöser-Sätzen wie „Feste suchen“, „Feste finden“.
3. Knoten **Frage**: „Wie heißt deine Kita oder wie lautet die Adresse?“, Erkennen: *Gesamte Antwort des Benutzers*, speichern als `Kita`.
4. Knoten **Frage** mit *Multiple-Choice-Optionen*: „bis 5 km“, „bis 7 km“, „bis 10 km“, „anderer Umkreis“, speichern als `Umkreis`. Diese Optionen erscheinen als Knöpfe.
5. Knoten **Frage** mit *Multiple-Choice-Optionen*: „nächste 4 Wochen“, „nächste 3 Monate“, „nächste 6 Monate“, „ganzes Jahr“, speichern als `Zeitraum`.
6. Knoten **Generative Antworten erstellen** (mit Websuche als Quelle). Als Eingabe einen Text mit den drei Variablen einsetzen: „Finde Feste für die Kita {Kita}, Umkreis {Umkreis}, Zeitraum {Zeitraum}“.
7. Testen, veröffentlichen und im Kanal **Microsoft 365 Copilot / Teams** freigeben.
Die Version mit Zahlen funktioniert ohne Copilot Studio sofort. Mit Studio wird es noch einfacher, aber die Einrichtung dauert länger.
