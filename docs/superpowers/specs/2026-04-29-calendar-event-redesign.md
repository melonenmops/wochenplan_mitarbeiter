# Calendar Event Redesign — Standort & saubere Darstellung

## Ziel

Kalender-Events sollen auf einen Blick verständlich sein: wer arbeitet heute, an welchem Standort.

## Scope

- Standort aus PDF-Header extrahieren (Marschacht / Garberscenter)
- Titel und Beschreibung der Events neu gestalten
- Namen alphabetisch sortieren
- Schicht-/Bereichslogik explizit NICHT implementieren (Zukunft)

## Architektur

### ParseResult-Dataclass (neu)

`PDFParser.parse()` gibt statt `Dict[str, List[str]]` ein `ParseResult` zurück:

```python
@dataclass
class ParseResult:
    days: Dict[str, List[str]]   # date_str → sorted names
    location: str = ""           # aus PDF-Header extrahiert
    # Erweiterungspunkte: source, shifts, warnings
```

Location-Extraktion: regex auf `Apotheke in/im <Name>` im PDF-Volltext.

### CalendarClient

- Kein `event_title` / `event_prefix` mehr im Konstruktor
- `upsert_event()` bekommt `location: str` Parameter
- Rückwärtskompatible Event-Erkennung: prüft `👥 Kollegen` UND altes `[WEEKLY_PLAN_COLLEAGUES]`

### Event-Format

**Titel:** `👥 Kollegen – Garberscenter`

**Beschreibung:**
```
Anwesende Kollegen (Garberscenter):
• Ahrens, Christina
• Al Hendi, Samir
• Brandt, Sonja
```

Bei leerer Liste:
```
Anwesende Kollegen (Garberscenter):

Keine anwesenden Kollegen gefunden.
```

### Geänderte Dateien

| Datei | Änderung |
|---|---|
| `app/pdf_parser.py` | `ParseResult`, `_extract_location()`, `parse()` return type, Namen sortiert |
| `app/calendar_client.py` | neues Titel/Beschreibungs-Format, `location` Parameter |
| `app/config.py` | `calendar_event_title` + `calendar_event_prefix` entfernt |
| `app/main.py` | Verdrahtung von `ParseResult.location` → `upsert_event()` |

## Nicht-Ziele

- Keine Schicht/Bereich-Erkennung
- Keine Farben (iCal unterstützt keine per-Event-Farben via CalDAV)
- Kein E-Mail-Betreff-Fallback (Struktur vorbereitet, nicht implementiert)
