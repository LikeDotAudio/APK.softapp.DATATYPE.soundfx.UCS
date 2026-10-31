# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Full text in LICENSE at the root.
"""The signature vocabulary and the .PEAK reader, once, for every script here.

    from ucs_vocab import VOCAB, FEATURES, LOG_AXIS, flatten_peak

`signature_vocabulary.json` (beside this file) is the one source: morphology
and separability enums, the available/proposed feature names, which features
must be log (`LOG_REQUIRED`), which a calibrator reads on a log axis
(`LOG_AXIS`), the 0..1-bounded and censored ones, and the .PEAK blocks
features come from. validate_signatures.py, fsd50k_calibrate.py and
music_calibrate.py import from here instead of restating their own sets — on
2026-10-30 three hand-written copies disagreed.

`flatten_peak(record)` is the single reader of a .PEAK sidecar's features: the
numeric scalars of the `peak_blocks`, plus the derived onset_rate_per_second
the scorer computes on the fly (ucs.rs feature()). Both calibrators use it.
No dependencies.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
VOCABULARY_FILE = HERE / "signature_vocabulary.json"

VOCAB = json.loads(VOCABULARY_FILE.read_text(encoding="utf-8"))

VERSION = VOCAB["version"]
MORPHOLOGY = frozenset(VOCAB["morphology"])
SEPARABILITY = frozenset(VOCAB["separability"])
FEATURES_AVAILABLE = frozenset(VOCAB["features_available"]["names"])
FEATURES_PROPOSED = frozenset(VOCAB["features_proposed"]["names"])
FEATURES = FEATURES_AVAILABLE | FEATURES_PROPOSED
LOG_REQUIRED = frozenset(VOCAB["log_required"]["names"])
LOG_AXIS = frozenset(VOCAB["log_axis"]["names"])
BOUNDED_0_1 = frozenset(VOCAB["bounded_0_1"]["names"])
CENSORED = {k: tuple(v) for k, v in VOCAB["censored"]["bounds"].items()}
PEAK_BLOCKS = tuple(VOCAB["peak_blocks"]["names"])


def consistency_errors():
    """What is wrong with the vocabulary file itself, as sentences (empty = fine)."""
    errors = []
    overlap = FEATURES_AVAILABLE & FEATURES_PROPOSED
    if overlap:
        errors.append(f"features both available and proposed: {sorted(overlap)}")
    for name, group in (("log_required", LOG_REQUIRED), ("log_axis", LOG_AXIS),
                        ("bounded_0_1", BOUNDED_0_1), ("censored", frozenset(CENSORED))):
        unknown = group - FEATURES
        if unknown:
            errors.append(f"{name} names features outside the vocabulary: {sorted(unknown)}")
    if not LOG_REQUIRED <= LOG_AXIS:
        errors.append(f"log_required not in log_axis: {sorted(LOG_REQUIRED - LOG_AXIS)} "
                      "(a calibrator would write linear for a feature the validator refuses as linear)")
    both = LOG_AXIS & BOUNDED_0_1
    if both:
        errors.append(f"features both log-axis and bounded 0..1: {sorted(both)}")
    for key, raw in (("morphology", VOCAB["morphology"]), ("separability", VOCAB["separability"]),
                     *((k, VOCAB[k]["names"]) for k in ("features_available", "features_proposed",
                                                         "log_required", "log_axis", "bounded_0_1"))):
        if len(raw) != len(set(raw)):
            errors.append(f"{key} lists a name twice")
    return errors


def flatten_peak(record):
    """A .PEAK sidecar (parsed JSON) -> {feature: number}. Booleans and non-numbers are dropped."""
    flat = {}
    for block in PEAK_BLOCKS:
        for key, value in (record.get(block) or {}).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            flat[key] = value
    # the scorer derives this on the fly; mirror it exactly (ucs.rs feature())
    if flat.get("length_seconds", 0) > 0 and "transient_count" in flat:
        flat["onset_rate_per_second"] = flat["transient_count"] / flat["length_seconds"]
    return flat
