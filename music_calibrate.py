#!/usr/bin/env python3
"""Calibrate the instrument categories' acoustic signatures against a real music library.

    python3 music_calibrate.py map                     # show which file-name role feeds which subcategory
    python3 music_calibrate.py measure   "<library>/"  # report only, writes nothing
    python3 music_calibrate.py calibrate "<library>/"  # measure, then rewrite the category files it touched

Why a second calibrator, next to fsd50k_calibrate.py
----------------------------------------------------
FSD50K is amateur audio, out of domain, and its labels come from a crosswalk. That is
why that script may only ever WIDEN a deviation: "a measured number is a prior on the
prior, and a too-tight prior produces confident wrong answers."

A producer's sample library is the opposite on every count. It IS the domain the
instrument categories (DRUMS, CYMBALS, PIANO, MALLET, ...) describe; it is clean,
professional, deliberately recorded audio; and it is the corpus the classifier will
actually be pointed at. Here a measured number is not a hint about the prior — it is
the thing the prior is trying to describe. So this script may tighten as well as widen,
and it says so in the provenance it writes.

The ground truth
----------------
Not the UCS matcher's own verdict — calibrating a classifier on its own output teaches
it only to repeat itself. The label is `classification.group`, the instrument the
SampleAnalyzer's file-name rules (PROCESSOR.SampleAnalyzer/src/NameSorting/
music_names.json, via label.rs) read off the name:

    "Kick_01.wav"   -> group Kick
    "Marimba C3.wav"-> group Marimba

That path never reads a UCS signature, so it is independent evidence.

Only the instrument categories are written — the 13 files exploded out of UCS MUSICAL,
told apart by their `version` (8.2.APK, not the published 8.2.1; see load_targets()).
Which subcategory a group calibrates is read off those files, never listed here:
a group feeds the one subcategory it names (Kick -> DRUMS/KICK, Crash -> CYMBALS/CRASH),
or failing a name, the one subcategory that lists it as a synonym (Conga -> DRUMS/HAND
DRUM). A group that names no subcategory, or more than one at the same rank (Splash is
CYMBALS/SPLASH and WATER/SPLASH), calibrates nothing and `map` says so. Run `map` before
`calibrate`: a generic group that lands by synonym (FX -> SYNTH/DRONE) is the category
data's word, not a judgement, and worth a look. MISC subcategories
are never calibrated: fitting "we could not tell" to the union of everything is exactly
the vague-but-always-plausible prior that makes MISC win.

This used to calibrate categories/MUSICAL.json and MUSICPROD.json against the 17 roles
of `classification.music_production_category`. Both files were split into the
instrument categories, MUSICPROD left UCS entirely (it is music_names.json now), and
the role field is no longer written, so the script loaded two files that do not exist.

The calibration policy and the spec are in the Scanalyzer:
SCANALYZER.Like.audio/README.md, "Calibrating the signatures against FSD50K", and
SCANALYZER.Like.audio/Documentation/Specs/ucs_signature_spec.md.
"""
import sys, os, re, json, math, glob, copy, statistics, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
# The day this run measured the corpus. Every prior, gate and evidence block it writes
# is stamped with it, so the date says when the number was taken, not when the script
# was first written. Gate records carried forward from an earlier run keep their own.
DATE = datetime.date.today().isoformat()

MIN_CLIPS = 40          # below this a median is an anecdote
LOG = {                 # features read in log space; deviation is a MULTIPLICATIVE factor
    'length_seconds', 'pitch_hz', 'spectral_centroid_hz', 'spectral_centroid_mean_hz',
    'spectral_centroid_deviation_hz', 'spectral_rolloff_hz', 'zero_crossings_per_second',
    'crest_factor', 'envelope_attack_seconds', 'envelope_decay_seconds',
    'envelope_release_seconds', 'decay_time_seconds_60db', 'onset_rate_per_second',
    'partial_count', 'transient_count', 'beats_per_minute',
}

# Features that describe the FILE rather than the SOUND, on any corpus.
#
# Deliberately much shorter than fsd50k_calibrate's NEVER list. Most of that list exists
# because Freesound uploads are amateur and inconsistently normalized — length is
# truncated, loudness is arbitrary, the codec sets the band limit. None of that is true
# of a professional sample library, where length and loudness are FACTS about the sample
# (a one-shot IS short; a mastered kick IS loud), so they are calibrated here.
NEVER = {
    'sample_rate',      # a property of the encoding
    'bit_depth',
    'dc_offset',        # a recording defect
    'clipping_density', # a defect
    'voicing_ratio',    # the WebRTC VAD is telephony-tuned; it fires on guitar and rain
}


def load_records(corpus):
    """Every .PEAK under the library, flattened to scalars + its independent role label."""
    out = []
    for path in glob.iglob(os.path.join(corpus, '**', '*.PEAK'), recursive=True):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue                       # legacy aggregate arrays
        group = (d.get('classification') or {}).get('group', '')
        if not group or group == 'Unclassified':
            continue
        c = {}
        for blk in ('metadata', 'envelope', 'spectral_features', 'musicality'):
            for k, v in (d.get(blk) or {}).items():
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                c[k] = v
        # the scorer derives this on the fly; mirror it exactly (ucs.rs feature())
        if c.get('length_seconds', 0) > 0 and 'transient_count' in c:
            c['onset_rate_per_second'] = c['transient_count'] / c['length_seconds']
        c['_group'] = group
        out.append(c)
    return out


def by_label(corpus, min_clips=MIN_CLIPS):
    recs = load_records(corpus)
    groups = collections.defaultdict(list)
    for c in recs:
        groups[c['_group']].append(c)
    kept = {k: v for k, v in groups.items() if len(v) >= min_clips}
    dropped = {k: len(v) for k, v in groups.items() if len(v) < min_clips}
    return kept, {'records': len(recs), 'labels': len(kept), 'too_few': dropped}


def values(clips, feat):
    v = [c[feat] for c in clips if feat in c and isinstance(c[feat], (int, float))]
    return [x for x in v if not (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))]


def robust(vals, feat, force_log=None):
    """median + MAD->sigma, in the space the caller will read it back in."""
    n = len(vals)
    if n < 8:
        return None
    log = (feat in LOG) if force_log is None else force_log
    x = [math.log(v) for v in vals if v > 0] if log else list(vals)
    if len(x) < 8:
        return None
    med = statistics.median(x)
    mad = statistics.median([abs(v - med) for v in x])
    sigma = 1.4826 * mad
    if sigma <= 0:
        s = sorted(x)
        sigma = (s[int(.84 * (len(s) - 1))] - s[int(.16 * (len(s) - 1))]) / 2.0
    return med, sigma, len(x)


def signif(x, digits=5):
    if x is None or x == 0:
        return 0.0 if x == 0 else None
    return round(x, max(0, digits - 1 - int(math.floor(math.log10(abs(x))))))


def calibrate_prior(p, clips):
    """Move the mean to the measured median and the deviation to the measured spread.

    Unlike the FSD50K path this may TIGHTEN. The corpus is in-domain, clean and large,
    so a narrow measured spread is a fact about the sound, not an artifact of the
    recording — and refusing to tighten would leave MUSICAL with the very vagueness that
    lets other categories outrank it on files that are plainly musical.
    """
    feat = p['feature']
    if feat in NEVER:
        return None
    v = values(clips, feat)
    if len(v) < MIN_CLIPS:
        return None
    log = p.get('transform') == 'log'
    st = robust(v, feat, force_log=log)
    if not st:
        return None
    med, sigma, n = st

    prov = p.get('provenance', {})
    old_mean = prov.get('reasoned_mean_before_calibration', p['mean'])
    old_dev = prov.get('reasoned_deviation_before_calibration', p['deviation'])

    new_mean = math.exp(med) if log else med
    if log:
        # a multiplicative factor: must stay > 1 or the scorer divides by ln(<=1)
        new_dev = max(math.exp(1.2 * sigma), 1.15)
    else:
        new_dev = max(1.2 * sigma, 1e-6)
    return signif(new_mean), signif(new_dev), n, old_mean, old_dev, log


def norm(word):
    """Spelling-blind key: 'Hi-Hat', 'hihat' and 'HI HAT' are one word."""
    return re.sub(r'[^a-z0-9]', '', word.lower())


def load_targets():
    """The instrument categories, by name -> (path, doc): the files this script may write.

    They are the ones exploded out of UCS MUSICAL, and the data says which: their
    `version` is APK's (8.2.APK), not the published UCS version index.json carries
    (8.2.1). The published categories (ALARMS/BELL, CLOCKS/CHIME, DESIGNED/TONAL) describe
    sound effects, and a music library is no evidence about them."""
    published = json.load(open(os.path.join(HERE, 'categories', 'index.json')))['version']
    out = {}
    for path in sorted(glob.glob(os.path.join(HERE, 'categories', '*.json'))):
        name = os.path.splitext(os.path.basename(path))[0]
        if name == 'index':
            continue
        doc = json.load(open(path))
        if doc.get('version') == published:
            continue
        out[name] = (path, doc)
    return out


def subcategory_for(targets):
    """Two indexes over every non-MISC subcategory: norm(name) and norm(synonym) -> {(file, sub)}."""
    names, synonyms = collections.defaultdict(set), collections.defaultdict(set)
    for name, (_, doc) in targets.items():
        for sub in doc.get('subcategories', []):
            label = sub['subcategory']
            if label == 'MISC':
                continue
            names[norm(label)].add((name, label))
            for word in sub.get('synonyms') or []:
                if norm(word):
                    synonyms[norm(word)].add((name, label))
    return names, synonyms


def resolve(group, index):
    """((file, subcategory), how) for a group, or (None, why) when it names none or several.

    A subcategory NAME outranks a synonym: Crash is CYMBALS/CRASH by name, though "crash"
    is also a synonym of every IMPACT and CRASH & DEBRIS."""
    names, synonyms = index
    for how, table in (('name', names), ('synonym', synonyms)):
        hits = table.get(norm(group), set())
        if len(hits) == 1:
            return next(iter(hits)), how
        if hits:
            return None, f'ambiguous {how}: ' + ', '.join(sorted(f'{f}/{s}' for f, s in hits))
    return None, 'names no subcategory'


def show_map(groups):
    """Print where each group would land. With no corpus, the analyzer's own instrument list."""
    targets = load_targets()
    index = subcategory_for(targets)
    feeds = 0
    for g in groups:
        where, why = resolve(g, index)
        if where:
            feeds += 1
            print(f"  {g:16} -> {where[0]}/{where[1]}   (by {why})")
        else:
            print(f"  {g:16}    ({why})")
    print(f"\n{feeds} of {len(groups)} groups feed exactly one subcategory")
    return feeds


def analyzer_groups():
    """The instrument names the SampleAnalyzer can put in classification.group."""
    path = os.path.join(HERE, '..', '..', 'PROCESSOR', 'PROCESSOR.SampleAnalyzer',
                        'src', 'NameSorting', 'music_names.json')
    seen = []
    for inst in json.load(open(path))['instruments']:
        if inst['instrument'] not in seen:
            seen.append(inst['instrument'])
    return seen


def run(corpus, write):
    kept, stats = by_label(corpus)
    print(f"corpus: {corpus}")
    print(f"  records with an independent group label : {stats['records']}")
    print(f"  groups with >= {MIN_CLIPS} samples          : {stats['labels']}")
    if stats['too_few']:
        print(f"  too few to calibrate (left alone)       : {stats['too_few']}")
    print()

    targets = load_targets()
    index = subcategory_for(targets)
    clips_for = {}                                   # (file, subcategory) -> clips
    for group, clips in kept.items():
        where, why = resolve(group, index)
        if where:
            clips_for.setdefault(where, []).extend(clips)
        else:
            print(f"  group {group!r} calibrates nothing ({why})")

    changes, touched = 0, set()
    for name, (path, doc) in targets.items():
        lines_out = []
        for sub in doc['subcategories']:
            label = sub['subcategory']
            clips = clips_for.get((name, label))
            if not clips:
                continue
            sig = sub.get('acoustic_signature') or {}
            priors = sig.get('priors') or []
            lines = []
            for p in priors:
                res = calibrate_prior(p, clips)
                if not res:
                    continue
                new_mean, new_dev, n, old_mean, old_dev, log = res
                tighter = new_dev < old_dev
                lines.append(f"      {p['feature']:38} mean {old_mean:>10.4g} -> {new_mean:<10.4g}"
                             f" dev {old_dev:>8.4g} -> {new_dev:<8.4g} "
                             f"{'TIGHTER' if tighter else 'wider  '} n={n}")
                if write:
                    prov = p.setdefault('provenance', {})
                    prov.setdefault('reasoned_mean_before_calibration', p['mean'])
                    prov.setdefault('reasoned_deviation_before_calibration', p['deviation'])
                    prov['calibrated_against'] = 'music production library'
                    prov['calibrated_on'] = DATE
                    prov['samples'] = n
                    prov['policy'] = ('in-domain corpus: the measured median and spread are '
                                      'authoritative, so the deviation may tighten as well as widen')
                    p['mean'] = new_mean
                    p['deviation'] = new_dev
                    changes += 1
                    touched.add(name)
            if lines:
                lines_out.append(f"  {label}  ({len(clips)} samples)\n" + '\n'.join(lines))
        if lines_out:
            print(f"=== {name}.json")
            print('\n'.join(lines_out))
        if write and name in touched:
            with open(path, 'w') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
                f.write('\n')
    print()
    if write:
        print(f"wrote {changes} priors across {len(touched)} category files: {sorted(touched)}")
        print("rebuild the engine: the revision hash covers the category data, so every")
        print("existing .PEAK sidecar is now stale and will be re-analyzed on the next scan.")
    else:
        print("measure only — nothing written. Re-run with `calibrate` to apply.")


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'map':
        sys.exit(0 if show_map(analyzer_groups()) else 1)
    if len(sys.argv) != 3 or sys.argv[1] not in ('measure', 'calibrate'):
        print(__doc__)
        sys.exit(2)
    run(sys.argv[2], write=(sys.argv[1] == 'calibrate'))
