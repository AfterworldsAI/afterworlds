# Retired Legacy SRD Artifact — CRD Issue 5c (#132)

This directory is a historical note only. The obsolete legacy SRD artifact and
its strict cross-store quarantine machinery have been **deleted** under the
pre-release clean baseline (Issue 5c Rev7 / Issue 18 Rev6). Nothing in the
running system reads, ingests, selects, publishes, or regenerates from the old
artifact; it survives only in Git history.

## What existed

- **File (deleted):** `srd_5_2_1_structured.legacy.json` — formerly the default
  ingestion input at `data/srd/srd_5_2_1_structured.json`, then quarantined here.
  It held 54 sections / 50 entities against a 364-page authoritative PDF; no code
  path or test ever derived, checked, or reconciled it against the source. Issue
  5c's concordance audit confirmed content/locator defects consistent with
  pre-5.2.1 (2014) material under a `5.2.1` tag (e.g. Cure Wounds `1d8` with an
  undead/construct exclusion vs SRD 5.2.1's `2d8` and no exclusion).
- **Former package identity:** name `D&D SRD 5.2.1`, version `5.2.1`.

## Pre-release clean baseline (owner decision)

Afterworlds is pre-release, so persistence created before Issue 5c receives no
upgrade-compatibility or preservation guarantee. The former strict
quarantine/zero-reachability contract (a repo+runtime reachability scan and a
publication-time legacy check) is **superseded**. The baseline instead:

1. deletes the incomplete SQL package and its dependent rows (migration `0018`);
2. deletes the obsolete JSON and retires every loader/default/seed/fallback/reader
   for it;
3. resets the configured development Chroma store in full once
   (`scripts/reset_corpus_baseline.py`) before rebuilding the corrected corpus;
4. rebuilds the rules-corpus projection only from the published Issue-5c
   SQLite-authoritative package.

Downstream consumers bind only to the new immutable corpus release produced by
the Issue 5c pipeline, which supersedes the retired artifact.
