# Exact-truth integration status

The [truth entry](../portable_truth/README.md) now supplies explicit prepared-input
and output paths, a byte-verified public Faiss wheel lock, the historical
add/search/write body, and a new receipt with frozen truth SHA and independent
raw-vector score checks. Original-data truth was not regenerated for delivery.

The old truth receipts did not identify the selected SIMD module. Current package
payloads match the wheel, but this does not retroactively attest runtime dispatch.
Future execution records dispatch and stops if any frozen truth SHA differs.

Next: bind the profile-stage native binaries, sixteen graph identities, and new
receipt schema. The historical profile launcher must not be run by deleting its
old audit or receipt checks. The complete raw-data-to-profile chain remains open.
