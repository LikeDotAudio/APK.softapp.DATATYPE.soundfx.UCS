# DATATYPE.soundfx.UCS

> 📑 **UCS sound-effects taxonomy, signed** — the Universal Category System v8.2.1 as JSON, one
> file per category, with an acoustic signature on every subcategory. It is the taxonomy the
> sample analyzer classifies against.
>
> 📚 **Wiki:** [Documentation/README.md](Documentation/README.md) — principles, architecture, delivery.

---

## 🧩 Architectural Role
* **Family**: DATATYPE — a data format other apps read; nothing here runs as a service
* **Category**: Sound-effects taxonomy (UCS v8.2.1) plus the calibration data behind its signatures
* **Pipeline Stage**: none of its own. It is compiled into `PROCESSOR.SampleAnalyzer` at build time and read by the Scanalyzer front end's synonym generator.

---

## ⚙️ What is in the repository

| Path | What it is |
|---|---|
| `categories/<CATEGORY>.json` | 94 files, one per category (`AIR` … `WOODWIND`; `&` is spelled `_` in the file name, e.g. `DIRT_SAND.json`). Each holds `version`, `category`, `emoji` and `subcategories[]`; every subcategory carries `subcategory`, `category_id` (e.g. `AIRBlow`), `explanation`, `synonyms` and an `acoustic_signature` (`morphology`, `separability`, `gates`, `priors`). 828 subcategories in all, every one signed. |
| `categories/index.json` | `version` `8.2.1`, `category_count` 94, and per category its file and `subcategory_count`. |
| `producer_synonyms.json` | Producer vocabulary ("808", "hihat", "oneshot") overlaid onto the instrument categories, keyed by `category_id`. Kept apart so the UCS files stay as published. |
| `fsd50k_crosswalk.json` | Hand map from FSD50K labels to UCS ids, each with a `high`/`medium`/`low` confidence, or `none` (refused, with a reason). |
| `fsd50k_calibration.json` | Record of the last FSD50K calibration: FSD50K.dev, 2026-10-30, 40 966 clips scanned, 22 915 used. Each run stamps the day it ran. |
| `fsd50k_separability.json` | 118 sibling-pair separability measurements (logistic probe accuracy vs. majority baseline), written by `fsd50k_calibrate.py separability`. |
| `UCS v8.2.1 Full Translations.xlsx` | The published UCS spreadsheet the JSON was built from. |
| `validate_signatures.py` | Checks every signature against the spec; exits non-zero on any error. |
| `fsd50k_calibrate.py` | Calibrates priors and gates from a folder of FSD50K `.PEAK` sidecars. |
| `music_calibrate.py` | Calibrates the instrument categories (`DRUMS`, `CYMBALS`, `MALLET` …) from a producer sample library — see below. |

The signature grammar, the closed feature vocabulary and the scoring math are specified in
`Softapps/SCANALYZER_SUITE/SCANALYZER.Like.audio/Documentation/Specs/ucs_signature_spec.md`.
The calibration policy is written up in the Scanalyzer README, section "Calibrating the
signatures against FSD50K". The scripts' docstrings cite both by those paths.

---

## 🚀 Usage & Integration

**Who reads it**

- `Softapps/PROCESSOR/PROCESSOR.SampleAnalyzer/build.rs` reads `../../DATATYPE/DATATYPE.soundfx.UCS/categories/*.json`
  and `producer_synonyms.json`, merges the overlay, minifies, and embeds the result
  (`include_str!` in `src/NameSorting/ucs.rs`). Changing a category file re-runs the build and
  restamps the analyzer version, which invalidates older `.PEAK` sidecars. A category file
  may opt out of matching with `"matchable": false`; none does today.
- `Softapps/SCANALYZER_SUITE/SCANALYZER.Like.audio/Web_Front/scripts/gen-ucs-synonyms.mjs`
  generates the front end's `src/ucsSynonyms.json` from the category files plus
  `producer_synonyms.json`.

**Validate** (no dependencies beyond Python 3):

```bash
python3 validate_signatures.py
```

Checked 2026-10-30: 828 subcategories, 828 signed, exit 0 ("every signature conforms to the
spec"), no warnings. A `confusable_with` id that names no subcategory, and a `provenance_only`
signature that carries priors, are errors: the 22 dangling ids the MUSICAL split left (`MUSC…`,
`CARTMisc`, `METALFric`, …) now name the instrument categories, and `VOXHist` lost its priors. A
log-normal feature (`MUST_BE_LOG`) on a `linear` transform is an error now, not a warning;
the 38 that were left were converted, each with a `transform_was_linear` provenance record.
The validator also checks `fsd50k_crosswalk.json`: every `ucs_id` must be defined by a category
file with the same category/subcategory, and the header counts must match the entries. The nine
retired `MUSC…` ids were re-pointed at the instrument categories; the broad parent labels
(`Drum`, `Guitar`, `Percussion`, …) are refused, so a `Snare_drum` clip still maps to one id.

**Calibrate** (each needs a corpus already scanned to `.PEAK`; run with no arguments for usage):

```bash
python3 fsd50k_calibrate.py evaluate  <FSD50K.dev_audio/>   # held-out 70/30, writes nothing
python3 fsd50k_calibrate.py calibrate <FSD50K.dev_audio/>   # rewrites categories/*.json and fsd50k_calibration.json
python3 fsd50k_calibrate.py separability <FSD50K.dev_audio/> # rewrites fsd50k_separability.json (needs numpy)
```

`music_calibrate.py` calibrates the 13 instrument categories exploded out of UCS MUSICAL
(the files whose `version` is `8.2.APK`) from a producer library scanned to `.PEAK`. Its
ground truth is `classification.group`, the instrument the SampleAnalyzer reads off the file
name; a group feeds the one instrument subcategory it names (or, failing that, lists as a
synonym). `map` prints that wiring without a corpus:

```bash
python3 music_calibrate.py map                     # 41 of 53 groups feed exactly one subcategory
python3 music_calibrate.py measure   <library/>    # report only
python3 music_calibrate.py calibrate <library/>    # rewrites the instrument category files it touched
```

**Web Portal Entry**: none. `display.json` declares the folder to the launcher
(`walk_project()` in `PODS/POD.THIN/WEB.OsApi/SRC/server.py`); its `entry`, `main.py`, is not a
file here, so the launcher opens the folder itself.
**Remote Repository**: `https://github.com/LikeDotAudio/APK.softapp.DATATYPE.soundfx.UCS.git`

---

## 🏛 Philosophy

- **One source of truth, compiled in.** The analyzer used to carry its own copy of the taxonomy
  and it drifted; `build.rs` now splices these files into the binary so the scorer and the
  taxonomy cannot disagree (`PROCESSOR.SampleAnalyzer/build.rs`, header).
- **The vendored standard stays pristine.** Producer words are an overlay
  (`producer_synonyms.json`) merged at build time, not edits to the UCS files
  (`build.rs`, overlay comment).
- **Say how far the signal can go.** Every subcategory declares a `separability` tier —
  `signal_separable`, `signal_narrowable`, `semantic_only`, `provenance_only` — so the
  classifier does not claim to hear what only a name can tell it (`categories/*.json`,
  enforced by `validate_signatures.py`, which also refuses a `signal_separable` tier that
  `fsd50k_separability.json` measures at chance).
- **A measured number is a prior on the prior.** FSD50K calibration may move a mean to the
  measured median but may only widen a deviation; eleven features that measure the uploader
  rather than the sound are never calibrated (`fsd50k_calibrate.py`, `NEVER`).
- **Provenance on every number.** A calibrated prior carries a `provenance` block naming the
  dataset and clip count; absence means "reasoned, never measured" (`categories/*.json`,
  `fsd50k_calibration.json`).
- **Closed vocabularies, checked by a machine.** Features, morphologies and tiers are fixed
  sets; `validate_signatures.py` refuses anything outside them.

<!-- wiki:smoke -->
**Smoke test** — ✅ PASS 1/1 since 2026-10-30 12:51 EDT — [results](Documentation/%F0%9F%A7%A9Manual%20and%20Artifacts/SMOKE.md)
<!-- /wiki:smoke -->
