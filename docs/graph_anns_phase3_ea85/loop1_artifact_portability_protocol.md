# Supplement Loop 1: artifact portability protocol

Objective: remove machine-specific execution assumptions without changing any
scientific result, frozen input, query role, seed, event, or gate.

Scope:

- parameterize Phase 1--4 launch and analysis scripts through explicit CLI or
  environment roots;
- retain current paths only as backward-compatible defaults;
- add a single master interface with `smoke`, `tables`, and documented `full`
  modes;
- validate from a neutral repository symlink/path using committed aggregates;
- update checksums only for new artifact metadata, never sealed scientific
  outputs.

Pass gate:

- no `/home/wlk` or server address in the anonymous artifact entrypoint;
- every historical hard-coded script has an explicit override;
- clean neutral-path smoke and table regeneration pass all focused tests;
- Phase 1--5 decision payloads and numerical tables remain byte-identical.

Stop immediately on input hash drift, any query-role change, any numerical
result change, or a need to access sealed raw truth. This loop contains no new
scientific experiment and cannot raise a scientific effect estimate.
