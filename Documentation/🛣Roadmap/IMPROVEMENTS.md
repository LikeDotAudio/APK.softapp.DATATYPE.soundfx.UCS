# 🛣 Improvements — DATATYPE.soundfx.UCS (from the 2026-10-30 architecture audit)

What this repo should change to meet the standard, most valuable first. Source: [🔍Audits/ARCHITECTURE-AUDIT.md](../%F0%9F%94%8DAudits/ARCHITECTURE-AUDIT.md).
← [Roadmap](INDEX.md)

Delivered items are in [🌍Publishing/DELIVERY.md](../%F0%9F%8C%8DPublishing/DELIVERY.md#delivered-from-the-2026-10-30-audit). Still open:

| # | Improvement | Category | Effort (S/M/L) | Evidence |
|---|---|---|---|---|
| 1 | Publish a release tag (e.g. `ucs-v8.2.1-apk.1`) for standalone consumers. **Needs owner** (tags are not published by agents); consumers in the monorepo pin by submodule commit meanwhile. | Change management | S | no tags |
| 2 | A `.PEAK` schema owned by SampleAnalyzer under `contracts/`; this repo's side (one reader, fields declared once in `signature_vocabulary.json`) is done. **Waiting on PROCESSOR.SampleAnalyzer / contracts (handoff filed).** | Boundary Integrity | M | `ucs_vocab.flatten_peak()` |
| 3 | The Scanalyzer replaces `Documentation/Specs/ucs_signature_spec.md` with a link to this repo's copy. **Waiting on SCANALYZER.Like.audio (handoff filed).** | Duplication Control | S | `Documentation/🧩Manual and Artifacts/ucs_signature_spec.md` |
