# musicxml-semantic-preflight

`musicxml-semantic-preflight` is a dependency-free checker for a narrow class of MusicXML hazards that can survive XSD validation but still change or destabilize a mature consumer's interpretation.

## Problem

MusicXML's XSD can establish structural validity without proving that a score's cross-element semantics are coherent. Public consumer reports describe schema-valid files with dangling paired spanners, incorrect measure-duration interpretation, or playback-jump semantics that are silently lost on import. A producer needs a fast, offline check before handing a file to a renderer, converter, or playback engine.

The first version is intentionally a **preflight witness**, not a repairer, importer, renderer, or claim of musical correctness.

## Candidate boundary

The initial investigation will test three checks:

1. paired-spanner balance and numbering for selected `start`/`continue`/`stop` elements;
2. measure-duration consistency where the MusicXML representation makes the expected duration computable;
3. explicit playback-jump references whose target semantics can be checked without guessing from prose.

The tool must report locations and typed outcomes such as `pass`, `warning`, `error`, or `unknown`. It must fail closed when the document does not contain enough evidence. It will not infer notation intent, repair a file, run a consumer, or certify compatibility.

## Evidence and uncertainty

- The W3C MusicXML specification and XSD define structural rules, but the project maintains open semantic-validation issues.
- MuseScore reports schema-valid inputs where explicit playback-jump attributes are imported as weaker text semantics under default settings.
- Audiveris reports exported files with missing or orphaned `octave-shift` stops that destabilize strict renderers.
- Existing validators inspected so far emphasize XSD, parse, or format validity; exact non-overlap with all mature consumers is not yet proven.

Demand and usefulness remain hypotheses until a real producer, importer, or maintainer confirms that these checks reduce a recurring workflow failure.

## Roadmap

1. Establish a small, secret-free fixture corpus from the documented hazard classes.
2. Define a deterministic report schema and explicit `unknown` states.
3. Implement only checks whose expected relation is supported by the MusicXML representation.
4. Run the corpus through at least one mature consumer as an observational comparison, without treating consumer acceptance as proof.
5. Stop and publish the boundary if the checks are useful; otherwise record the falsifier and archive the repository.

## Validation method

- deterministic fixture input and byte-stable JSON output;
- unit tests for balanced, unbalanced, ambiguous, and incomplete cases;
- XML parsing and path/location checks;
- `python -m compileall` and `git diff --check` for the initial implementation;
- an explicit comparison against the exact checks provided by one mature consumer or validator.

## Try the witness

The first offline witness is a single-file CLI using only the Python standard library:

```bash
python3 preflight.py score.musicxml
python3 preflight.py score.mxl
python3 -m unittest discover -s tests -v
```

The JSON report is deterministic and separates `error`, `warning`, `unknown`, and `pass`.
The initial implementation checks only balanced `slur`, `tied`, and `octave-shift` spans,
single-voice computable measure duration, and explicit playback-jump targets. Multiple
voices and incomplete timing evidence are reported as `unknown`; no repair or musical
intent inference is attempted.

## Falsifier and stopping point

This project is falsified if a maintained, accessible validator already provides the same typed paired-spanner, duration, and playback-semantic preflight with equivalent location-rich output, or if real producer/consumer evidence shows the checks are too ambiguous to act on safely.

The stopping point is one deterministic fixture corpus, one reviewable integration sample, and documented limitations. No provider adapters, GUI, automatic repair, semantic music interpretation, network service, or LLM feature will be added without a concrete consumer-shaped request.

## Sources

- W3C MusicXML specification and MusicXML 4.0 XSD: <https://github.com/w3c-cg/musicxml>, <https://www.w3.org/2021/06/musicxml40/listings/musicxml.xsd/>
- MuseScore import semantics report: <https://github.com/musescore/MuseScore/issues/33801>
- Audiveris paired-spanner export report: <https://github.com/Audiveris/audiveris/issues/933>
