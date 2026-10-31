# 🔍 Architecture audit — DATATYPE.soundfx.UCS (2026-10-30)

Audited against the APK.audio multi-repo architecture standard: coupling, boundaries, duplication, contracts.
← [Audits](INDEX.md) · Improvements: [🛣Roadmap/IMPROVEMENTS.md](../%F0%9F%9B%A3Roadmap/IMPROVEMENTS.md)

## Bounded context
The sound-effects taxonomy: UCS v8.2.1 as JSON (94 `categories/*.json`, 828 signed subcategories, `categories/index.json`), the producer-vocabulary overlay, the FSD50K crosswalk and the calibration record, plus three Python tools (`validate_signatures.py` 268 lines, `fsd50k_calibrate.py` 694, `music_calibrate.py` 344). Data repo, no service. Sampled: all scripts, `display.json`, `categories/AIR.json`, `categories/.gitignore`, and the two known consumers.

## Context map
| Talks to | How (topic / endpoint / file / import) | Relationship |
|---|---|---|
| `PROCESSOR.SampleAnalyzer` | its `build.rs:30-36` reads `../../DATATYPE/DATATYPE.soundfx.UCS/categories` and `producer_synonyms.json` by relative path and `include_str!`s the result | Supplier → Customer, but through a file path, not a versioned artifact |
| `SCANALYZER.Like.audio` Web_Front | `scripts/gen-ucs-synonyms.mjs` reads the category files to build `src/ucsSynonyms.json` | Supplier → Customer (file path) |
| `Documentation/🧩Manual and Artifacts/ucs_signature_spec.md` (here) | the signature grammar; moved here 2026-10-30; the Scanalyzer's copy is now a pointer | Own published language |
| SampleAnalyzer `.PEAK` sidecars | one reader, `ucs_vocab.flatten_peak()`, used by both calibrators; fields = the vocabulary's `features_available` | Conformist, through one adapter; schema: SampleAnalyzer `SRC/core/schema/peak.schema.json` |
| WEB.OsApi walker | `display.json` → `index.html` (the one UCS taxonomy tile) | Conformist |

## Scorecard
| Category | Score (0–3) | Finding |
|---|---|---|
| Coupling & Cohesion | 3 | The spec lives with the data and the bundle is a cargo package a consumer pins by `rev` (delivered). |
| Boundary Integrity | 3 | Category files have a JSON Schema; `.PEAK` goes through one reader and its schema is SampleAnalyzer's `peak.schema.json` (delivered). |
| Duplication Control | 3 | One vocabulary file for the validator and both calibrators; the disagreement is reconciled (delivered). |
| Testing & Contracts | 3 | `python3 validate_signatures.py && python3 -m unittest test_ucs_vocab` is the single local check (delivered); no CI, per the root's decision. |
| Change management | 2 | Vocabulary versioned and a data changelog kept (delivered); no git tag for standalone consumers — needs owner. |
Score key: 3 meets the standard · 2 minor gaps · 1 significant gaps · 0 absent / violated.

## Findings
1. **Good — data kept as published.** Producer slang lives in `producer_synonyms.json`, an overlay keyed by `category_id`, so the UCS files stay as the standard publishes them; the source spreadsheet is tracked beside the JSON.
2. **No release tag.** Consumers pin the cargo package by git `rev`; a tag such as `ucs-v8.2.1-apk.1` for standalone consumers needs the owner to publish it.
3. **Good — the validator checks cross-file integrity** (dangling `confusable_with`, crosswalk ids resolve to a defined subcategory, header counts match), and now the vocabulary's own consistency and the schema's enums.

Delivered items were removed from this page; see [🌍Publishing/DELIVERY.md](../%F0%9F%8C%8DPublishing/DELIVERY.md#delivered-from-the-2026-10-30-audit).
