# Owner Decision - SRD 5.1 contest procedure as an Afterworlds v1 supplement

Recorded on 14 October 2026 for CRD Issue 15b (#127). This record covers the Owner's policy and source
choice only. It is not acceptance of an authority candidate, an implementation, a publication or an
activation.

## Owner direction

The Owner rejected the proposed deferral of #127 acceptance criterion 8:

> Opposed/contested rolls are integral to the RPG experience. They occur dozens of times within a short
> adventure and hundreds of times within a campaign. They must be resolvable within v1. That doesn't
> mean they have to be in 15b, but unless there is another more appropriate place to put them in, they
> should go here.

Codex then asked whether to adopt the SRD 5.1 contest rule as an explicit supplement. The reviewed
proposal was `PROPOSED-OPPOSED-CHECK-CONTRACT.md`, SHA-256
`6e708e77dcbe3fefcd3d0cef7aaf9fdff2c3ee783b9e3d3df3b8f01a3d338a20`. The Owner answered **"Adopt this
explicit contest supplement"**. Codex recorded that answer in
`CONTEST-SUPPLEMENT-OWNER-ACCEPTANCE-2026-10-14.md`, SHA-256
`fcc30b1ba6370bb02e35521130f437dee82ec55e0aacfc3b0e06cf2a5ed8af03`. Both files are coordination
artifacts outside the repository.

## Accepted policy

CRD Issue 15b delivers generic two-party ability/skill contests in v1. It uses the official SRD 5.1
"Contests" procedure as an explicit Afterworlds supplement:

1. Code compares the participants' authoritative final check totals; the greater total wins.
2. Equal totals preserve the situation that existed before the contest. No automatic reroll or
   universal acting-side win is implied.
3. Applicable specific SRD 5.2.1 mechanics remain unchanged unless separately overridden. Hide's
   recorded-result DC, Influence's formula DC and Grapple/Shove's saving throws are not silently
   converted into generic contests.

Only the contest procedure is adopted. SRD 5.1 is not imported wholesale.

## Source

| Field | Value |
|---|---|
| Document | System Reference Document 5.1 (Creative Commons edition), CC-BY-4.0 |
| URL | https://media.dndbeyond.com/compendium-images/srd/5.1/SRD_CC_v5.1.pdf |
| SHA-256 | `2504d2a0abb0a4d491a939be4f17910a2dde0312570ab8d208080225ccf0a1f0` (3,158,713 bytes) |
| Section | "Contests", printed page 77 (PDF page index 76) |

## Boundaries

- The supplement is explicit, versioned, bound and auditable. It is not an undocumented adapter
  fallback, and it is not an SRD 5.2.1 fact.
- Accepted C8 and its source and acceptance identities are preserved.
- Criterion 8 remains positive execution.
- Any new authority artifact still needs independent review and exact semantic acceptance before
  dependent implementation. That includes the supplement override S1 and the creature-skill candidate
  C9, both under `.claude/review-notes/issue-15b-contest-authority/`.
- Publication, activation, migration and merge each need separate authorization.
- The comparison and equality policy is settled. Do not ask the Owner to choose it again.

The resulting contract is ADR-015b Group 17 (15b-37). That text is proposed and awaits Owner acceptance
of the whole PR.

## Acceptance (2026-10-14)

The Owner accepted PR #194 at `5d05f473` and the native C9 review packet, including the combat Action
cost (receipt `.claude/review-notes/issue-15b-c9-recording/owner-acceptance-2026-10-14.md`). Group 17
(15b-37), S1 (`c232a786…`) and C9 r2 (`a3d40545…`) are accepted; the text above is kept as the
pre-acceptance record. C9 is recorded natively as `srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json`
(`01729b53…`). S1 is not recorded in the corpus and is not activated: it stays a release-bound authored
override applied only to isolated in-memory fixtures until a separately authorized operational gate.
PR #129's explicit resume gate is not released by this acceptance.
