# Separate source-design NDC phase

The historical E1a source response contains IDs/recall/CP decisions but no NDC.
`source_counter.py` supplies the separate original full500-query, 11-action
counter replay. Its schema remains `query_ids`, `action_grid`, `ndc`, rather
than silently adding counts to the earlier source response.

Use a source response request as described in README, adding `source_panel`
(the complete new16-unit source lock), `profiles_adapter` and `native_build`.
`graphs.fixed` and `truths.fixed` bind the graph and design truth; source roles
and native arrays are pinned before use. The newly exported E1AQ0001 query
file must match its original SHA and size. The unchanged new-built replay500
binary runs once with real wait, then ordered IDs/hits/absolute-failure events
are compared to the frozen source response. The resulting NDC array must match
the distinct historical array pin.

```sh
python portable_transfer_1m/source_counter.py --request /path/to/source-counter.json \
  --input-adapter portable_fresh_inputs --output /path/to/NEW-source-counter \
  --outstanding-growth-bytes 137438953472 --authorize-source-counter
python -m unittest discover -s portable_transfer_1m -p test_source_counter.py -v
```

The original historical100-query pilot receipts are not rerun or fabricated.
The new native build's synthetic equivalence checks establish the new interface;
full output hash gates establish data identity for any future requested run.
Source NDC is descriptive work, not wall-clock time or lifecycle acquisition
seconds. CPU2,24GiB AS,128MiB file/output,600CPU seconds/900wall seconds apply,
with existing project RAM/disk preflight unchanged. No source-data run was
performed during this delivery preparation. Pins were retrieved read-only from
the original panel and two query receipts; their hashes appear in the addendum.
