# Mature-consumer overlap review

Reviewed 2026-09-21 against public primary sources.

## Findings

### W3C specification repository

The W3C Music Notation Community Group has an open validation issue stating that a `<tie>` or `<tied>` element on a rest is allowed by the standard but does not make musical sense. This is direct evidence that the schema boundary does not exhaust semantic validation.

Source: <https://github.com/w3c-cg/musicxml/issues/673>

### MuseScore

MuseScore issue #33801 gives a minimal MusicXML 4.0 file that validates against the W3C schema but loses explicit `dacapo`/`fine` playback semantics under default import settings. Even with inference enabled, the importer can reduce `D.C. al Fine` to a plain `D.C.` jump. MuseScore's regression tests also did not exercise the default setting or distinguish the round-tripping representations.

Source: <https://github.com/musescore/MuseScore/issues/33801>

This is a mature-consumer behavior boundary, not a claim that a producer-side checker can predict every MuseScore result. A first version may only flag explicit, mechanically observable jump references and must label consumer-specific behavior as outside its proof.

### Audiveris

Audiveris issue #933 reports missing or orphaned `<octave-shift>` stops, including zero-length and end-of-part spans. The issue describes how one missing stop can cascade into new numbering and cause strict renderers to crash or render incorrectly. Audiveris issue #653 separately reports exported measures missing after rhythm/time-signature problems.

Sources: <https://github.com/Audiveris/audiveris/issues/933>, <https://github.com/Audiveris/audiveris/issues/653>

Audiveris is therefore overlapping evidence for the problem, but not an existing standalone preflight with a portable, location-rich, typed report.

## Decision

The candidate survives this overlap review narrowly. Create the first implementation only for representation-level checks that can be stated without consumer-specific heuristics:

- paired-spanner balance and number reuse where the format exposes a start/continue/stop relation;
- computable measure-duration mismatches, with `unknown` for cases requiring notation inference;
- explicit playback-jump references as a warning/evidence check, not a guarantee of playback behavior.

Do not implement a MuseScore emulator, an Audiveris repairer, a general musicality checker, or automatic fixes. The falsifier remains a maintained tool that already exposes this same narrow report boundary or a real user test showing that the report is not actionable.
