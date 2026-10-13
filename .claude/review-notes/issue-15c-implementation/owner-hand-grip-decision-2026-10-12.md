# CRD Issue 15c — bounded hand/grip input: APPROVED

Direct Owner answer in this chat, 12 October 2026 (Pacific).

Question: “For CRD Issue 15c, may the GameMaster supply auditable hand/grip facts through code-generated options for a named subject and identified held items? This would support free-hand loading, Two-Handed and Versatile rules. Code would validate holdings, source requirements, conditions, conflicts and revisions, and invalidate affected facts after grip/item changes. Missing or contradictory facts refuse; these facts cannot create ammunition, waive requirements or grant actions. Your earlier spatial approval did not explicitly cover hand occupancy. I recommend this bounded input instead of a general inventory simulator.”

Owner answer: **“Approve bounded hand/grip facts (recommended)”**.

This resolves the hand-input branch in `codex-c7-boundary-classification.md`. Code-generated options must name the subject and actual held items, preserve source hand/grip requirements, validate conditions/conflicts and current revisions, and invalidate affected facts after grip or item changes. An `equipped` flag alone is not proof of wielding or complete hand occupancy. Missing/contradictory state refuses. This adds no general inventory simulator, ammunition, action grant or waiver of source requirements.

The decision accepts no new C7 semantic fact, schema or successor identity. C7 still requires the independently reviewed exact native simulated preview and explicit Owner semantic acceptance before real recording or dependent authority execution. The original C6/r2 packets remain immutable and unaccepted; C6-B remains withdrawn. Continue approved implementation and preview preparation in the same CRD Issue 15c PR. No merge, shared-runtime migration, publication/activation or app launch; #129 open/frozen, #132/#137 unchanged.
