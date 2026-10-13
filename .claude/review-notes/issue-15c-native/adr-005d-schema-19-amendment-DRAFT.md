# DRAFT — ADR-005d amendment, representation schema 19 (CRD Issue 15c)

REVIEW MATERIAL ONLY. This is not applied to `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` and is not accepted. It would be inserted after the schema-18 amendment, and only if the Owner accepts the exact native preview identities in `OWNER-ACCEPTANCE-PACKET.md` and the successor is then recorded natively.

---

> **Amendment — representation schema 19 (CRD Issue 15c, Owner acceptance PENDING).**
> Schema 19 (`5d-representation-schema-19`, hash `3734ccf7d6be7f25e0a0d7c0395121c5525afcb87144f5cf9d6895e03c1cd18f`) admits the independently reviewed C5 bounded-d20 source contract. It adds:
>
> - **126 declarative fact families.** These cover:
>   - creature attacks, saves, Multiattack, entry usage and references;
>   - observer checks, conditional defenses and sizes;
>   - typed clause pieces (`clause_*`) with their entry, section, part and piece addresses;
>   - rule, weapon, tool and notation facts;
>   - the contributing grants (skill, save, weapon, armor, tool, feat, ability increase, expertise and Weapon Mastery).
> - **The 135 vocabularies minted with those families**, each wholly new.
> - **Four omit-when-empty `WeaponPropertyFact` fields:** `ammunition`, its normal and long range, and the Lance's `unless`.
>
> **Scope.** No accepted family, field or vocabulary changes meaning. The registered lift `5d-lift-schema-18-to-19` proves every previously accepted payload byte-identical under 19.
>
> **`tool_activity` is an identity, not a rule.** It is the selectable identity of each of the 34 C5 tool activities. Its vocabulary is exactly the reviewed C5 option keys. A tool with two or more activities is a native choice: one option per activity, each carrying the tool's common facts. A single-activity tool states its activity directly. The activity text stays governed prose.
>
> **Intrinsic contract.** The schema declares its rules in the invariant manifest, so weakening one moves the hash:
> - exactly-one and at-most-one field pairs;
> - property-bound weapon fields;
> - integer domains for every integer field;
> - nested dice and rationals held to their accepted rules.
>
> **Decision 4 still holds.** Each family states what the source prints. Execution, applicability and certification are code-owned capability, not this union. A use with no certified capability fails closed, so admitting a family does not make it executable.
>
> **Recording (pending).** The Owner would accept the exact eleven replacement proposals and the resulting successor oracle (identities in the packet). They would be recorded natively as a same-release successor to `srd-5-2-1-corpus-8781d4e0-a3b-g1.json`. G1 would be kept byte for byte and skipped by digest, so the release keeps one claimant. The other 13 accepted batches keep their acceptance rows byte-identical.
