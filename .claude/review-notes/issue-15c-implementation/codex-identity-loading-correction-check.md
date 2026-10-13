# CRD Issue 15c — identity/loading correction check

Two delivery findings are addressed in the inspected working changes on parent head `9477e766c6b1bd13940fdb959e9e78a4fd35e12c`; implementation was not yet committed when checked. `economy.py` SHA-256 `eccc6825b8f6a047f9e26e1e576378ca10ba0aa4d27fbec49d3cb7156085e4bb`; `hands.py` SHA-256 `74da351abc2753ca6f241615ac1dec73e768fe3caf0d8cb41fac78978c214a0e`. Reuse only if final source matches; this is not final-head acceptance.

Follow-up at 12:08 UTC: committed as `2570029cdf50590d0b764eeb627791ba665e7b9a`, with both inspected hashes unchanged. Associate the check with this commit; later creature/discovery/spatial corrections still require review.

Source inspection: attack use retains both accepted source record and actual item UUID; Light/Nick compares the UUID while checking source Light properties. Free-hand loading classification comes from the accepted Two-Handed property independently of declared grip. Existing physical holdings/grip validation remains. The all-ammunition helper now gives one-handed weapons a free hand.

Independent real-adjudication probe reuses the original reviewer script, preserved unchanged. The new `delivery-review/recheck_identity_loading.py` explicitly constructs the two-hand/zero-free-hand assertion, so the changed test helper cannot hide the original regression. `identity-loading-recheck.jsonl` records:

- distinct held Daggers: successful Light composition, four dice calls;
- Hand Crossbow gripped in two hands with zero free hands: `invalid_selection`, zero dice;
- same weapon held with one required free hand: success, two dice calls.

The existing Push → actor edges → Wolf Pack Tactics scenario still accepts stale nearby-ally facts. That known separate finding remains pending; no claim of delivery-family closure or full acceptance. No source/store/authority changes, full suite, app launch or CI was performed by this check. Engineer's new same-item/Nick regressions and targeted E2E require their own actual exit/evidence; the probe above establishes the principal corrected source behaviors independently.
