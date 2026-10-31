#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Full text in LICENSE at the root.
"""Tests: one vocabulary, one .PEAK reader, and a validator that fails when it should.

    python3 -m unittest -v test_ucs_vocab
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import ucs_vocab
import fsd50k_calibrate
import music_calibrate

HERE = pathlib.Path(__file__).resolve().parent
TRACKED = ["validate_signatures.py", "ucs_vocab.py", "signature_vocabulary.json", "category.schema.json",
           "fsd50k_crosswalk.json", "fsd50k_separability.json", "categories"]


class OneVocabulary(unittest.TestCase):
    def test_vocabulary_is_consistent(self):
        self.assertEqual(ucs_vocab.consistency_errors(), [])

    def test_calibrators_share_it(self):
        self.assertIs(fsd50k_calibrate.LOG, ucs_vocab.LOG_AXIS)
        self.assertIs(music_calibrate.LOG, ucs_vocab.LOG_AXIS)
        self.assertEqual(fsd50k_calibrate.VOCABULARY, ucs_vocab.FEATURES)
        self.assertIs(fsd50k_calibrate.BOUNDED_0_1, ucs_vocab.BOUNDED_0_1)

    def test_required_log_is_on_the_log_axis(self):
        # the 2026-10-30 disagreement: band_limit_high_hz was required-log but not on a calibrator's axis
        self.assertLessEqual(ucs_vocab.LOG_REQUIRED, ucs_vocab.LOG_AXIS)
        self.assertIn("band_limit_high_hz", ucs_vocab.LOG_AXIS)

    def test_flatten_peak(self):
        record = {"metadata": {"length_seconds": 2.0, "is_stereo": True, "name": "x"},
                  "spectral_features": {"spectral_centroid_hz": 1200},
                  "musicality": None,
                  "envelope": {"transient_count": 4},
                  "classification": {"group": "Kick", "score": 0.9}}
        self.assertEqual(ucs_vocab.flatten_peak(record), {
            "length_seconds": 2.0, "spectral_centroid_hz": 1200, "transient_count": 4,
            "onset_rate_per_second": 2.0})


class ValidatorFails(unittest.TestCase):
    """Run validate_signatures.py on a scratch copy and break one thing at a time."""

    def run_on(self, mutate):
        with tempfile.TemporaryDirectory() as scratch:
            root = pathlib.Path(scratch)
            for name in TRACKED:
                source = HERE / name
                (shutil.copytree if source.is_dir() else shutil.copy)(source, root / name)
            mutate(root)
            return subprocess.run([sys.executable, "-I", str(root / "validate_signatures.py")],
                                  capture_output=True, text=True, cwd=root)

    def test_clean_copy_passes(self):
        self.assertEqual(self.run_on(lambda root: None).returncode, 0)

    def test_unknown_feature_fails(self):
        def mutate(root):
            path = root / "categories" / "AIR.json"
            data = json.loads(path.read_text())
            data["subcategories"][0]["acoustic_signature"]["priors"][0]["feature"] = "loudness_vibes"
            path.write_text(json.dumps(data))
        result = self.run_on(mutate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown feature 'loudness_vibes'", result.stdout)

    def test_schema_enum_drift_fails(self):
        def mutate(root):
            path = root / "category.schema.json"
            schema = json.loads(path.read_text())
            schema["$defs"]["signature"]["properties"]["morphology"]["enum"].append("wobble")
            path.write_text(json.dumps(schema))
        result = self.run_on(mutate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("morphology enum differs", result.stdout)

    def test_vocabulary_inconsistency_fails(self):
        def mutate(root):
            path = root / "signature_vocabulary.json"
            vocab = json.loads(path.read_text())
            vocab["log_axis"]["names"].remove("band_limit_high_hz")
            path.write_text(json.dumps(vocab))
        result = self.run_on(mutate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("log_required not in log_axis", result.stdout)


if __name__ == "__main__":
    unittest.main()
