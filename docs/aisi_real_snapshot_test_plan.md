# AISI Real Snapshot Test Plan

## Ziel des Testplans
Den aktuellen CV-Table-Stand über mehrere reale Snapshots gegen die AISI-Pipeline testen, ohne die allgemeine CV-Pipeline umzubauen. Fokus ist die stabile Übergabe eines einzelnen Snapshot-Zustands an AISI.

## Bestehende Annahmen
- Der Table-Pfad in CV ist als brauchbare Grundlage vorhanden.
- Chairs und Persons sind nicht Teil des Kern-Interfaces.
- AISI benötigt pro Test nur einen einzelnen Snapshot-Zustand, keine Zeitreihe.

## Minimales Interface CV -> AISI
Der Export soll nur dieses Format liefern:

```json
{
  "roi": {
    "x_min": 0.0,
    "x_max": 500.0,
    "y_min": 0.0,
    "y_max": 500.0
  },
  "tables": [
    {
      "id": "table_0",
      "x": 0.0,
      "y": 0.0,
      "rot_deg": 0.0,
      "width": 140.0,
      "depth": 70.0
    }
  ]
}
```

Pflichtfelder pro Tisch:
- `id`
- `x`
- `y`
- `rot_deg`
- `width`
- `depth`

## Empfohlene 5 reale Testszenen
1. Clean frontal
2. Messy
3. Leichte Occlusion
4. Verschobener Tisch
5. Enge Tischsituation

## Pro Test zu prüfende Punkte
- Tischanzahl korrekt?
- Position plausibel?
- Rotation plausibel?
- Erzeugt AISI für `input`, `groupwork`, `discussion` sinnvolle Ergebnisse?

## Fehlerklassifikation
- Exportproblem: CV erzeugt falsches oder unvollständiges AISI-JSON.
- CV-Snapshotproblem: Der Snapshot selbst ist unbrauchbar, unvollständig oder inkonsistent.
- AISI-Robustheitsproblem: Export ist okay, aber AISI verarbeitet den Fall nicht stabil oder plausibel.

## Minimales Testprotokoll pro Lauf
- Snapshot-Datei
- Format
- erkannte Tischanzahl
- Score
- Positionen plausibel? ja/nein
- Rotationen plausibel? ja/nein
- Ergebnis plausibel? ja/nein
- Fehlerklasse
- Kurznotiz

## Nächste Entscheidung nach den Tests
Wenn mindestens 4 von 5 Szenen stabil durchlaufen, den CV->AISI-Export als Integrationsbasis festschreiben und nur noch Ausreißer gezielt nachziehen. Wenn weniger stabil, zuerst die Fehlerklasse trennen und den schwächsten Pfad fixen.
