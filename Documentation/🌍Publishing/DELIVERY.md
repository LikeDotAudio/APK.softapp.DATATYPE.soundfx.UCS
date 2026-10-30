# Delivery — DATATYPE.soundfx.UCS

← [Wiki home](../README.md)

**Nothing to build here.** The data ships inside other things:

| Where it lands | How |
|---|---|
| **the SampleAnalyzer binary** | `PROCESSOR.SampleAnalyzer/build.rs` embeds `categories/*.json` and `producer_synonyms.json` at `cargo build`; `rerun-if-changed` on both, so an edit here rebuilds and restamps the analyzer. Whatever image or desktop build carries the analyzer carries this data. |
| **the Scanalyzer front end** | `gen-ucs-synonyms.mjs` regenerates `src/ucsSynonyms.json`, which ships in the Scanalyzer's `Web_Front/dist/` |
| the rig, as files | baked into the **WEB.Frontend-Assets** image with the rest of `PODS/POD.THIN/Softapps` (`up-stack.sh WEB.Frontend-Assets` after an edit) |
| apk.audio, as files | uploaded with the whole monorepo checkout by its `.github/workflows/ci.yml` FTPS job when the submodule pointer is bumped (`.apk.scripts/deploy_all.py`). There is no page to open — `display.json`'s `entry` (`main.py`) is not a file here. |

Remote: `https://github.com/LikeDotAudio/APK.softapp.DATATYPE.soundfx.UCS.git` (no workflow of its own).

**Tested:** by hand — `python3 validate_signatures.py` (exit 0 on 2026-10-30, 23 warnings) and `python3 music_calibrate.py map`. The SampleAnalyzer's `cargo test` exercises the embedded table (`ucs::tests`). `.apk.scripts/smoke.py` checks only that HEAD is pushed ([SMOKE](../%F0%9F%A7%A9Manual%20and%20Artifacts/SMOKE.md)).

**Not automated:** nothing runs the validator on push; recalibration needs a scanned corpus and is run by hand; after an edit, rebuilding the analyzer and regenerating `ucsSynonyms.json` are separate manual steps.
