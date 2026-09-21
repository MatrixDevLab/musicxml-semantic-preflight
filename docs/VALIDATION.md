# Validation method

The project is considered useful only if its claims remain narrower than the evidence.

1. Fixtures are hand-reviewed and contain no private or copyrighted score material.
2. Each fixture states the expected typed result and the exact relation being tested.
3. The command output is compared byte-for-byte across repeated runs.
4. Malformed and incomplete inputs must produce `unknown` or a typed parse failure rather than a guessed pass.
5. The fixture corpus is observed through at least one mature MusicXML consumer, but consumer acceptance is recorded as evidence, not as semantic proof.
6. The final README records checks that are not covered, including musical intent, engraving quality, and provider-specific import behavior.
