# Architecture — DATATYPE.soundfx.UCS

← [Wiki home](../README.md)

A data repo: JSON other code reads, plus three Python scripts that check and calibrate it. Nothing here runs as a service.

## The data

| Path | What |
|---|---|
| `categories/<CATEGORY>.json` | 94 files, one per category (`&` spelled `_`: `DIRT_SAND.json`). Each: `version`, `category`, `emoji`, `subcategories[]`; every subcategory has `subcategory`, `category_id`, `explanation`, `synonyms` and an `acoustic_signature` — `morphology`, `separability`, `gates[]` (hard limits), `priors[]` (`feature`, `mean`, `deviation`, `transform` `log`/`linear`, `weight`, `provenance`). 81 files are published UCS (`version: "8.2.1"`); 13 instrument categories (`BRASS`, `CYMBALS`, `DRUMS`, `GUITAR`, `KEYBOARD`, `LOOPS`, `MALLET`, `PERCUSSION`, `PIANO`, `STRINGS`, `SYNTH`, `VOCALS`, `WOODWIND`) were exploded out of UCS MUSICAL and carry `version: "8.2.APK"`. |
| `categories/index.json` | `version`, `category_count`, and per category its file and `subcategory_count`. |
| `producer_synonyms.json` | producer vocabulary overlaid onto the instrument categories at build time, keyed by `category_id` |
| `fsd50k_crosswalk.json`, `fsd50k_calibration.json`, `fsd50k_separability.json` | the FSD50K label map, the record of the last calibration, and 118 sibling-pair separability measurements (`fsd50k_calibrate.py separability`; both files regenerated 2026-10-30 against the MUSICAL-split ids) |
| `UCS v8.2.1 Full Translations.xlsx` | the published spreadsheet the JSON was built from |

## Who reads it

- **`PROCESSOR.SampleAnalyzer/build.rs`** splices `categories/*.json` plus the overlay into one array in `OUT_DIR`; `src/NameSorting/ucs.rs` embeds it with `include_str!` and scores every sound: gates first, then a weighted Gaussian over the priors (`signal_likelihood()`; a `log` prior compares `ln x` with `ln mean` over `ln deviation`). A change here re-runs the build and restamps the analyzer version, so older `.PEAK` sidecars go stale.
- **`SCANALYZER.Like.audio/Web_Front/scripts/gen-ucs-synonyms.mjs`** generates the front end's `src/ucsSynonyms.json` from the same files.

## The scripts

```bash
python3 validate_signatures.py                     # every signature against the spec, and the FSD50K crosswalk against categories/; exit 1 on any error
python3 fsd50k_calibrate.py evaluate  <FSD50K/>    # held-out 70/30, writes nothing
python3 fsd50k_calibrate.py calibrate <FSD50K/>    # widen-only calibration of categories/*.json
python3 fsd50k_calibrate.py separability <FSD50K/> # sibling-pair logistic probe -> fsd50k_separability.json
python3 music_calibrate.py map                     # which file-name instrument feeds which subcategory
python3 music_calibrate.py measure   <library/>    # in-domain calibration, report only
python3 music_calibrate.py calibrate <library/>    # rewrites the instrument category files it touched
```

Both calibrators read `.PEAK` sidecars (the SampleAnalyzer's output), never audio. `fsd50k_calibrate.py` joins FSD50K file-name labels to UCS ids through the crosswalk. `music_calibrate.py` labels each clip by `classification.group` (the instrument the analyzer reads off the file name — `music_names.json`), maps the group to the one instrument subcategory it names or lists as a synonym (`resolve()`), and writes median and MAD-derived spread with a provenance block. Python 3 standard library only, except `separability`, which needs numpy. A re-run of `calibrate` drops gate history whose `ucs_id` no category file defines any more.
