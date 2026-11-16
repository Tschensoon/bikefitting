# Langdock-Agent „Kita-Radar“: Einrichtung

Recherche-Agent für Kita-Schließungen, vorübergehende Schließungen und relevante Träger-/Betreiberwechsel in allen 16 Bundesländern, mit Fröbel-Nähe-Priorisierung und Abdeckungsprotokoll.

## 1. Grunddaten (Agent anlegen → „Neuer Agent“)
| Feld | Eintrag |
|---|---|
| Name | Kita-Radar Deutschland |
| Beschreibung | Recherchiert aktuelle Kita-Schließungen und Trägerwechsel in jeder Region Deutschlands, prüft Primärquellen, dokumentiert die Quellenabdeckung und priorisiert Fälle nahe Fröbel-Kitas. |
| Icon | 🏫 oder 🔎 |
| Anweisungen | kompletter Inhalt von `01_anweisungen.md` |

## 2. Modell
**Empfehlung: Claude Opus, die neueste Version in eurem Langdock-Workspace.**
Gründe:
- Die Aufgabe ist eine lange, mehrstufige Webrecherche mit vielen Regeln (Ereignistypen, Quellenhierarchie, Widersprüche, Protokoll). Opus hält solche Anweisungen über viele Suchschritte am zuverlässigsten ein.
- Opus kennzeichnet Unsicherheit gut und erfindet seltener Quellen oder Daten. Das ist hier das wichtigste Kriterium.
- Gutes Deutsch und saubere große Tabellen.

Alternative für schnelle Einzelanfragen (ein Kreis, eine Stadt): **Claude Sonnet** (neueste Version). Das geht schneller und günstiger, ist bei flächendeckenden Läufen aber weniger gründlich. Bei Bedarf einen zweiten Agenten „Kita-Radar Schnellcheck“ mit Sonnet anlegen.

Kreativität/Temperatur: **niedrig** (Regler ganz links bzw. ≤ 0,2). Für Recherche zählt Genauigkeit.

Langdock legt das Modell pro Agent fest und wählt es nicht pro Anfrage automatisch. Deshalb Opus als Standard setzen und Nutzer bei Bedarf im Chat auf Sonnet wechseln lassen, falls euer Workspace den Modellwechsel im Agenten-Chat erlaubt.

## 3. Fähigkeiten
| Fähigkeit | Einstellung | Wofür |
|---|---|---|
| Websuche | **an (Pflicht)** | Recherche, Seiten öffnen |
| Datenanalyse / Code | **an** | Luftlinien-Vorauswahl der nächsten Fröbel-Kitas aus der CSV, CSV-Export |
| Canvas | optional an | Ergebnistabelle bearbeiten/exportieren |
| Bildgenerierung | aus | nicht benötigt |

## 4. Wissen (Dateien hochladen)
1. `02_skill_source-coverage-research.md`: der Skill `source-coverage-research`
2. `03_regionen-referenz.md`: Gebietseinheiten und Pflichtquellen aller Bundesländer
3. `froebel-standorte.csv`: Fröbel-Standorte im Format von `04_froebel-standorte_vorlage.csv` (Name, Straße, PLZ, Ort, Bundesland, Kontakt, lat/lon, Stand-Datum). Die Datei bitte aus der offiziellen Standortübersicht befüllen und regelmäßig aktualisieren. Ohne diese Datei liest der Agent die Standortsuche auf froebel-gruppe.de live. Das ist langsamer und weniger zuverlässig.

## 5. Konversationsstarter
- Flächendeckende Recherche Hamburg und Schleswig-Holstein, Standardeinstellungen
- Schnellcheck: Kita-Schließungen in [Stadt/Kreis] der letzten 2 Monate
- Kita-Schließungen im Umkreis von 10 km um Fröbel-Kitas in [Bundesland]
- Aktualisiere meine Ergebnisliste (Liste einfügen)
- Welche Gebiete und Quellen sind noch offen?

## 6. Optional: echte Straßenentfernung per Aktion
Ohne Aktion liefert der Agent einen anklickbaren OpenStreetMap-Routenlink und kennzeichnet Werte als „Luftlinie“ oder „Schätzung“. Für berechnete Straßenkilometer eine eigene Integration in Langdock anlegen (Integrationen → Eigene Integration):
- **Geocoding**: `GET https://nominatim.openstreetmap.org/search?q={adresse}&format=json&limit=1&countrycodes=de`. Einen eigenen User-Agent-Header setzen und höchstens 1 Anfrage pro Sekunde senden (Nutzungsrichtlinie).
- **Route**: `GET https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false`, dann `routes[0].distance / 1000` = km.
- Aktion „Route berechnen“ nennen. Die Anweisungen nutzen sie automatisch, wenn sie vorhanden ist.
- Die öffentlichen Demo-Server sind nur für geringe Last gedacht. Bei regelmäßiger Nutzung einen eigenen OSRM/Nominatim-Server oder einen kommerziellen Dienst (z. B. Google Routes API, HERE) einsetzen. Dann den Namen der Routenquelle in den Anweisungen anpassen, damit alle Vergleiche dieselbe Quelle nutzen.

## 7. Nutzung (interaktiv)
- Der Agent fragt zuerst Gebiet, Modus (Schnellcheck/flächendeckend), Radius und Zeitraum ab. Wer „Standard“ antwortet, startet sofort.
- Große Bundesländer (z. B. Bayern mit 96 Einheiten) werden in Etappen bearbeitet. Mit „weiter“ geht es zur nächsten Etappe, mit „Export“ kommt die Gesamttabelle als CSV.
- Für Aktualisierungen die letzte Ergebnistabelle einfügen. Der Agent markiert dann NEU / GEÄNDERT / UNVERÄNDERT / ERLEDIGT.

## 8. Test vor dem Freigeben
1. „Flächendeckende Recherche Schleswig-Holstein“: Prüfen, ob die Abdeckungsübersicht vor den Ergebnissen steht und alle 15 Einheiten auflistet.
2. „Kita-Schließungen in Bremerhaven, Radius 5 km“: Prüfen, ob der Filter greift und die Entfernungsart gekennzeichnet ist.
3. Eine Region ohne Treffer: Der Agent muss klar „keine bestätigten Fälle“ melden.
