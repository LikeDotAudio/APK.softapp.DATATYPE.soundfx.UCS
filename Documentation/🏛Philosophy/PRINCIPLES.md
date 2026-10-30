# Principles — DATATYPE.soundfx.UCS

The rules this taxonomy keeps, each with the file or function that keeps it. Ecosystem rules are cited, not copied: [Refusal over fabrication](../../../../../../../Documentation/%F0%9F%8F%9BPhilosophy/Doctrine/readme.Refusal%20over%20fabrication.md). The signature grammar itself is specified in the Scanalyzer: `SCANALYZER.Like.audio/Documentation/Specs/ucs_signature_spec.md`.

← [Wiki home](../README.md)

| Principle | Kept by | Where it breaks |
|---|---|---|
| **One source of truth, compiled in.** The analyzer once kept its own copy and it drifted; now it embeds these files. | `PROCESSOR.SampleAnalyzer/build.rs` header and its `rerun-if-changed` on `categories/` (lines 3–10, 28–29) | — |
| **The vendored standard stays pristine.** Producer words are an overlay merged at build time, not edits to the UCS text. | `producer_synonyms.json`; the merge in `build.rs` | The 13 instrument categories exploded out of UCS MUSICAL are APK's own (`version: "8.2.APK"`), not published UCS |
| **Say how far the signal can go.** Every subcategory declares a separability tier, so the classifier does not claim to hear what only a name tells it. | `acoustic_signature.separability` in `categories/*.json`; enum checked in `validate_signatures.py` (line 85) | — (a `provenance_only` signature with priors is a validator **error**; `VOXHist`'s were dropped 2026-10-30) |
| **Log-normal features are scored in log space.** | `MUST_BE_LOG` (`validate_signatures.py` line 55) — a `linear` transform on one is an **error** | — (the last 38 were converted 2026-10, each with a `transform_was_linear` record) |
| **A measured number is a prior on the prior.** FSD50K is out of domain, so its calibration may only widen a deviation, and features that measure the uploader are never calibrated. | `NEVER` (`fsd50k_calibrate.py` line 49); `new_dev = max(old_dev, …)` in `calibrate_prior()` (lines 238, 240) | — |
| **In-domain evidence may tighten, but never the classifier's own verdict.** The music calibrator labels each clip by the file-name instrument (`classification.group`), never by the UCS match. | `load_records()` and `calibrate_prior()` in `music_calibrate.py` | — |
| **No hard-coded mapping.** Which subcategory a group calibrates, and which files may be written, are read off the category data. | `load_targets()` (version ≠ published), `subcategory_for()` / `resolve()` in `music_calibrate.py` | — |
| **Provenance on every number.** A calibrated or converted prior names its dataset, clip count and the value it replaced; absence means "reasoned, never measured". | `provenance` blocks in `categories/*.json`; written by both calibrators | — |
| **Closed vocabularies, checked by a machine.** | `MORPHOLOGY`, `FEATURES` (`validate_signatures.py` lines 16–51) | — (a `confusable_with` id that names no subcategory is an **error**; the 22 left by the MUSICAL split were re-pointed at the instrument categories 2026-10-30; a crosswalk `ucs_id` no category file defines is an error too, and its nine retired `MUSC…` ids were re-pointed the same day) |
