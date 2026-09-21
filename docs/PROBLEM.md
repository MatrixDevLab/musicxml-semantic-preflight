# Problem statement

## User

The likely first user is a developer or pipeline maintainer producing MusicXML for a renderer, notation editor, converter, or playback system. They need a cheap preflight signal before an import silently loses meaning or emits a malformed cross-element relation.

## Smallest useful release

A local command that accepts one `.musicxml` or `.mxl` file and emits deterministic, location-rich JSON for a deliberately small set of checks. Every result must distinguish a proved failure from an unsupported or incomplete case.

## Non-goals

This is not a general MusicXML validator, a notation-quality grader, a repairer, a renderer, or a replacement for consumer-specific regression tests.

## Open questions

- Which semantic relations are both common enough and mechanically decidable?
- Can the report remain useful without claiming that a consumer will render or play the score correctly?
- Does a producer actually act on a preflight report, or only discover failures after opening the file?
