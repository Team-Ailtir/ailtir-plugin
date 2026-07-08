# Classification Heuristics

## 1. What this reference is

This note explains, for the Claude assistant driving the project-indexer
skill, how `scripts/classify.py` decides whether each PDF in a tender
pack is a **drawing**, a **document**, or `unsure`, and how to walk a
user through borderline cases before any vision call is spent on a
sheet. The classifier is deterministic and offline — it reads the
discovery inventory only, never the PDF itself. Treat it as triage
whose job is to keep downstream cost proportional to confidence.

## 2. The signal table

The classifier accumulates a drawing-ness score in `[0, 1]`. Structural
signals come from the PDF metadata already captured by `discover.py`
(media-box size, orientation, first-page character count, page count).
Filename signals come from the stem itself. Folder signals come from
the immediate parent directory name. A score above **0.7** commits to
`drawing`; below **0.3** commits to `document`; the middle band lands
as `unsure` and is queued for review.

For the exact weights per signal, consult `spec_project-indexer_classify.md`,
the canonical source that `classify.py` implements. In summary:

- **Structural signals** favour drawings when the sheet is A0–A2 or
  tabloid, landscape, first page has fewer than ~400 characters, and
  total page count is small. They lean towards documents on A4 or US
  letter, high character counts, or many pages.
- **Filename signals** carry more weight than structural ones because a
  filename encodes the author's intent. An ISO 19650 `Type=DR` is worth
  roughly twice any single structural cue; `SP`/`RP`/`SH`/`MS`/`HS` in
  the Type field is a decisive document vote.
- **Folder signals** ratify the filename. Parent folders like
  `04. Drawings` or `Sheets` add drawing weight; `Correspondence`,
  `Reports`, `Contract`, `Programme` or `Specifications` subtract it.

Every fired signal is recorded on the file's `classification.signals`
array so a reviewer can see, in one glance, which cues produced the
score.

## 3. Ailtir profile awareness

Under the `ireland-gc` and `uk-gc` profiles, sheet-size expectations
are sharper than in a US project. Consultants working to RIBA Plan of
Work stages or under the Public Works Contract Framework produce work
in a small set of predictable formats:

- Working drawings issue on **A1 landscape**, with A3 landscape
  reductions circulated as coordination copies.
- **Specifications**, **Schedules of Works** and **contract documents**
  (PW-CF suites in Ireland; JCT and NEC suites in the UK) are A4 portrait.
- **Bills of Quantities** and **Pricing Documents** are usually A4
  portrait but occasionally land as landscape XLSX-exported PDFs
  because NRM2 description columns will not fit portrait.
- **Programmes** exported from Asta Powerproject or Primavera P6 are
  landscape, often A3.

Because letter-size paper is essentially absent from the Irish and UK
market, a "landscape letter" PDF that would be inconclusive in a US
context is treated as document-leaning here — no legitimate drawing
office issues sheets on that stock.

## 4. ISO 19650 filename signals

Recent Irish and UK projects follow ISO 19650-2 naming:

```
<Project>-<Originator>-<Volume>-<Level>-<Type>-<Role>-<Number>-<Status>-<Revision>
```

The two-character **Type** field is decisive. `DR` means the container
is a 2D drawing; `SP`, `RP`, `SH`, `MS`, `HS`, `CO`, `MI` and the other
text-container codes all mean the container is a document. When a
filename parses cleanly the Type signal outweighs almost every
structural cue — an A4 portrait scan named `…-DR-A-…` is still a
drawing (usually a detail); an A3 landscape export named `…-RD-…` is
still a programme. See `research/drawing-conventions.md` for the full
Type list, Role letters, S/A/B status codes and revision formats.

## 5. Common edge cases

- **Pre-2015 scanned drawings.** CWMF-era A1 scans; the structural
  signal fires but first-page character count is near zero. Usually
  commits `drawing`; a truncated scanner media box drops it into
  `unsure`.
- **JCT or PW-CF tender pack cover pages.** A4 portrait, no vectors,
  filename says "Drawings issued with tender". Classified `document`.
- **BOQ or Pricing Document in landscape.** A4 or A3 landscape with
  very high character density from NRM2 columns; character-count
  penalty overrides the landscape drawing hint.
- **Programme prints from Asta or P6.** A3 landscape, thousands of
  Gantt-bar vectors. Structural signals shout drawing; the filename
  token `Programme` or ISO 19650 Type `RD` is the tie-breaker.
- **Site logistics plans.** A3 landscape, high vector count. Genuinely
  drawings; classifier says so and the user chooses a trade
  perspective for downstream analysis.
- **PSDP-issued Health & Safety Plans.** A4 portrait, image-heavy from
  hazard photographs and risk-assessment tables. Classified `document`.
- **Coordination drawings embedded in a specification.** Structural
  signals split; lands `unsure`. Usually treated as a document because
  the surrounding pages are text.
- **GA sheet with a schedule tacked on.** Still a drawing; the schedule
  is embedded on-sheet and structural signals catch it.
- **Prelims and bid-response templates.** A4 portrait, dense text or
  form-like. Classified `document`.
- **CIRI or Safe-T-Cert certificates and PII schedules.** A4 portrait,
  image-heavy from letterheads and stamps. Classified `document`.

## 6. Handling borderline output

The SKILL.md's Step 2 iterates every file whose score sits in the
middle band and shows the user its fired signals so the decision is
transparent. The user chooses `drawing`, `document`, or `skip`, and
the answer is written back into `/tmp/project_classified.json` so the
file is not re-prompted on subsequent runs. The dialog looks like:

```
File: 04. Correspondence/2024-11-14 - Response to RFI-042.pdf
Score: unsure (drawing-ness 0.42)
Signals fired:
  + A3 landscape                            +0.15
  + landscape orientation                    +0.10
  + folder contains "correspondence"        −0.30
  + filename contains "RFI"                  −0.10
Recommend: document
> [d]ocument / d[r]awing / [s]kip? _
```

Always show the fired signals with signs. Users trust a decision they
can audit; they do not trust a bare probability.

## 7. Override strategies

If a user has a project-specific rule ("everything starting with `AR-`
or `ST-` is a drawing"), they can supply a pattern list at the top of
Step 2 that short-circuits the score for matching files. The current
SKILL.md does not formalise this — it is a documented future extension
pending user demand.

## 8. When to re-classify

If a misclassification surfaces later (typically when the drawings
analysis pass complains a PDF has no title block), the user has two
remedies: delete the affected file's classification block in
`/tmp/project_classified.json` and re-run `classify.py`, or manually
edit `kind_pdf` and append `"human_override"` to the `signals` array so
the change is visible on subsequent audits. Either path is safe — the
downstream drawings-analysis and document-summarisation steps re-read
the classification JSON on each invocation, so corrections propagate
without a full re-index.
