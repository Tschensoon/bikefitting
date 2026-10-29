# Aufgaben-Board für Outlook

Outlook-Add-in, das ein Kanban-Board (Zu erledigen, In Arbeit, In Prüfung, Erledigt) als Seitenleiste neben deinen E-Mails öffnet.

- Kennzahlen: offen, fällig diese Woche, überfällig, erledigt in den letzten 7 Tagen
- Filter nach Projekt, Priorität, Fälligkeit und Freitext
- Aufgabe direkt aus der geöffneten E-Mail anlegen (Betreff wird Titel, die E-Mail bleibt verknüpft und lässt sich von der Karte aus öffnen)
- Schmale Seitenleiste: eine Spalte pro Reiter, Pfeil-Knopf schiebt die Karte weiter. Breite Ansicht: alle Spalten nebeneinander mit Drag & Drop
- Seitenleiste lässt sich anheften und bleibt beim Wechsel der E-Mail offen

Die Aufgaben werden in den Roaming-Einstellungen des Add-ins in deinem Postfach gespeichert. Sie sind damit in Outlook im Web, im neuen Outlook und im klassischen Outlook gleich. Microsoft begrenzt diesen Speicher auf 32 KB, das reicht für etwa 150 Aufgaben. In der Spalte „Erledigt“ kannst du alte Aufgaben aufräumen.

## Einrichten

### 1. Dateien über GitHub Pages bereitstellen (einmalig)

1. Im Repository auf **Settings → Pages** gehen.
2. Bei **Source** „Deploy from a branch“ wählen, Branch `main` und Ordner `/docs` einstellen, speichern.
3. Nach ein bis zwei Minuten muss https://tschensoon.github.io/bikefitting/outlook/taskpane.html das Board zeigen.

### 2. Add-in in Outlook hinzufügen

1. `manifest.xml` aus diesem Ordner herunterladen.
2. https://aka.ms/olksideload öffnen (Outlook im Web). Das Fenster „Add-Ins für Outlook“ geht auf.
3. **Meine Add-Ins → Benutzerdefinierte Add-Ins → Benutzerdefiniertes Add-In hinzufügen → Aus Datei hinzufügen** und `manifest.xml` wählen.
4. Das Add-in steht danach auch im neuen Outlook und im klassischen Outlook zur Verfügung (gleiches Konto).

### 3. Benutzen

E-Mail öffnen, dann **Apps** (bzw. das „…“-Menü) → **Aufgaben-Board**. Mit dem Pin-Symbol oben in der Seitenleiste bleibt sie offen.

## Dateien

| Datei | Zweck |
| --- | --- |
| `manifest.xml` | Beschreibt das Add-in für Outlook (Knopf, Symbol, Adresse der Seitenleiste) |
| `taskpane.html` / `.css` / `.js` | Die Seitenleiste selbst |
| `assets/` | Symbole in 16 bis 128 px |
