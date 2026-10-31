# Changelog — DATATYPE.soundfx.UCS data

What changed in `categories/*.json` (and the vocabulary that governs them), newest first. A
calibrator rewrite (`fsd50k_calibrate.py calibrate`, `music_calibrate.py calibrate`) adds a line
here in the same commit as the rewritten files: the date it ran, the corpus, and what moved.
Consumers (PROCESSOR.SampleAnalyzer `build.rs`, the Scanalyzer's `gen-ucs-synonyms.mjs`) see a
data change as a restamp of the analyzer version.

← [Wiki home](../README.md)

| Date | Commit | Change |
|---|---|---|
| 2026-10-30 | (this audit) | `signature_vocabulary.json` 1.0.0: one vocabulary for the validator and both calibrators; `log_axis` reconciled (fsd50k now reads `spectral_centroid_deviation_hz` on a log axis like music; music now reads `band_limit_high_hz` and `complexity` on a log axis, as the validator requires for the former). No category file changed. `category.schema.json` added. |
| 2026-10-30 | `3caea50` | WATRBubl and WATRDrip set to `signal_narrowable` after the FSD50K separability probe measured them at chance. |
| 2026-10-30 | `75238c0` | Calibrators stamp the day they ran, not a hard-coded 2026-07. |
| 2026-10-30 | `11da349` | FSD50K calibration and separability regenerated on the MUSICAL-split ids. |
| 2026-10-30 | `175e1fe` | No dangling `confusable_with` ids; VOXHist without priors. |
| 2026-10-30 | `eb3e8eb` | Log-normal priors use the log transform; the validator refuses linear. |
| 2026-09-13 | `a05a042` | Initial import of UCS v8.2.1 with acoustic signatures. |
