# Committed accepted oracles — CRD Issue 5d

One JSON file per published CRD Issue 5c release, holding the accepted
meaning-bearing authority the publication gate judges a persisted projection
against: the exact release binding, the declared semantic policy, the accepted
span classification, the accepted record/component/fact/prose-binding/
relationship/reference/provenance inventory, and the accepted per-record
obligations.

The schema is whatever `oracle.load_oracle` accepts; it rejects a missing key,
an extra key, and an undeclared enum value rather than defaulting any of them.

**This directory is deliberately empty of production content.** No accepted
oracle exists for the SRD 5.2.1 release yet, so that release resolves to no
accepted authority and its mechanical projection cannot be published — which
is the honest state until the accepted full-corpus authority is reviewed and
committed by a later CRD Issue 5d content PR.

Files here are review artifacts, not build output. Nothing in `src/` writes to
this directory, and no oracle may be generated from a candidate or from
persisted projection state: an oracle derived from the thing it checks proves
only that the code agrees with itself.
