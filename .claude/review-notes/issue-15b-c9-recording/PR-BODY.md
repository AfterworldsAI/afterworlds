CRD Issue 15b needs the accepted creature-skill authority before its contest lifecycle can resume. This PR records C9, lands schema 22 with it, and recertifies the existing 15c operations together. It is stacked on accepted, unmerged #194.

C9 adds the reviewed printed Skills facts to 336 profiles. The recorded file's SHA-256 is `01729b532a0ff46047608d9e46d539851ba2c9a32aaa9e0468ae0babb902ec7b`; its semantic identity and projection equal the accepted native packet. Only acceptance evidence differs from the simulated preview. C8 bytes and the 20 untouched batches' receipts are preserved. Packaging selects C9 and retains C8 as source history.

All 14 admitted operations certify against C9 with unchanged governing fingerprints. C8 certificates refuse, and changed creature profiles receive new template digests. A separate in-memory S1/C9 compatibility proof preserves the accepted S1/C8 report. No contest adapter or lifecycle is implemented here.

The PR also records the accepted schema/Group 17/Action-cost status and fixes collection-dependent Story/Node registration in ingestion test setup. The sibling fixture gaps outside ingestion are recorded and deferred.

### Validation

Native recording: zero findings, clean persist/reconstruct/re-identify, passing read-only gate. Affected diagnostics include 27 publication tests, 26 published API/packaging tests, 806 RPG/state tests, 1,391 mechanical consumers and 325 other consumers. The fixture fix passed the two-node reproduction and 140 affected tests. Earlier failed diagnostics remain documented in the recording notes.

Black, Ruff, strict mypy and the secret hook passed. The checksum baseline is narrowly audited and a new-value negative control still fails detection as expected. Unchanged accepted source/native proofs were reused; no full local suite with coverage was repeated. Final exact-head CI is pending.

### Architecture Notes

No drift from design principles. This is ADR-015b Group 17's authority landing gate, under the Owner's exact #194/native-packet acceptance. Adapter/manifest versions remain unchanged because operation behavior and fingerprints are unchanged; the projection identifies the new certification.

PR #129 remains frozen at `d8233a435b6b7bf11cc043786570063027ccec57`, with its explicit resume gate preserved. No Phase 3 or 19b work, merge, shared-runtime migration, shared publication or activation. Runtime publication/rebinding and S1 activation remain separately authorized operations.
