# Classification Heuristics

How `scripts/classify.py` distinguishes drawings from documents, and how to handle edge cases.

## Signals used

| Signal | Drawing-like | Document-like |
|---|---|---|
| Max sheet dimension | > 900pt (larger than A3) | ≤ 900pt (A4 / letter / smaller) |
| Orientation | Landscape | Portrait |
| Text chars per page | < 400 | > 1500 |
| Vector drawings per page | > 50 | < 10 |

Each signal contributes to a drawing_score or document_score. If one score beats the other by 2+, that's the classification. Otherwise it's flagged **borderline** for human review.

## Why these signals

- **Sheet size** is the strongest discriminator. Drawings are issued on A1/A2/A3 sheets; documents live on A4. A contract or spec being printed on A4 is ~100% reliable in practice.
- **Orientation** helps but isn't decisive — some specifications use landscape tables, some drawings use portrait orientation for schedules.
- **Text density** separates prose-heavy documents from label-heavy drawings. Combined with size, it's very reliable.
- **Vector drawings per page** captures the reality that drawings have hundreds of lines, arcs, and polygons; documents mostly have text and the occasional image.

## Common edge cases

### Scanned drawings (image-only PDFs)
Vector count will be near zero and text will also be near zero. The size signal will still identify them as drawings in most cases. If the scan has been reduced to A4, they'll end up borderline — surface to the user.

### Mixed documents (drawings embedded in a spec PDF)
Rare but real. Tender PDFs sometimes bundle sketches with written specifications. Classifier will call these borderline or document. Ask the user whether to process as drawings; most of the time they'll want them treated as documents because the drawing quality is poor.

### Schedules (door, window, fixture, finishes)
Schedules presented on drawing sheets are drawings. Schedules presented as Excel exports to PDF are documents. Either way the classifier usually gets it right on size alone.

### Cover sheets and drawing registers
Sometimes issued at A4 by mistake. If size signal puts them as document but the user expects them as drawings, let them override — it doesn't matter much because a cover sheet doesn't need deep per-sheet analysis.

### Reports with plan extracts
Geotechnical reports, surveys, heritage reports — these are landscape-ish, often A3, with some vector content. Can end up borderline. Default them to **document** unless the user wants them treated as drawings.

## Human review protocol

When the classifier flags anything borderline:

1. Show the user the file path, the reasons, and ask.
2. If they're unsure, default to the safer option. The safer option is usually **document** — misclassified documents cost less token-wise than misclassified drawings (which get full vision analysis).
3. Record their decision in the classification output for re-runs.

## Overrides

If the user has a file-naming convention (e.g. all drawings start with a sheet code like `A-101`), you can apply that as a pre-filter alongside the heuristics. Ask once at the start of the run if they have such a convention.
