"""CRD Issue 15c C8 -- revalidate the captured native preview after the
codex-c8-schema-code-review P2 correction (relational validation only).

The correction changes ``validation._validate_summoned_creature_types`` and
nothing the preview's bytes depend on, so the built snapshot is not rebuilt.
This script proves that rather than assuming it:

- the captured preview, its five proposals and the schema-21 hash are the
  exact pinned bytes the build produced (``reports/c8-preview.json``);
- re-identification gives the same projection and payload hash;
- the builder's own ``native`` stage reruns under the corrected code:
  ``validate_candidate``, the five malformed variants, private-store
  persist/reconstruct/re-identify, the own gate and the cross-gates;
- every Find Familiar form in the preview is a direct, unconditional profile
  (one size, one Beast type, no options, applicability or qualifiers);
- the four conditional-scope variants the review demonstrated, built from the
  preview's own ``animals.cat`` profile, are refused through
  ``validate_candidate``.

Writes ``reports/c8-revalidation.json``. Run from the preview worktree root
with the checkout's ``src`` on ``PYTHONPATH``::

    python .claude/review-notes/issue-15c-c8-native/revalidate_c8_preview.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_c8_preview as b  # noqa: E402

from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    Applicability,
    ApplicabilityKind,
    ComponentOption,
    FactQualifier,
    Phase,
)

c = b.c
REPORT = json.loads((b.HERE / "reports/c8-preview.json").read_text("utf-8"))
VALIDATION = b.REPO / "src/afterworlds/ingestion/mechanical/validation.py"
CAT = ("animals.cat", "cat")
NEEDLE = "summoned_creature_type names animals.cat/cat"
WHILE_ACTIVE = Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE)


def _is(fact: object, kind: type) -> bool:
    return type(fact) is kind


def _conditional(comp: Any, case: str) -> Any:
    if case == "option_arms":
        typeless = tuple(f for f in comp.facts if not _is(f, b.CreatureTypeFact))
        return dataclasses.replace(
            comp,
            facts=(),
            options=(
                ComponentOption(semantic_key="a", facts=comp.facts),
                ComponentOption(semantic_key="b", facts=typeless),
            ),
        )
    if case == "component_applies_when":
        return dataclasses.replace(comp, applies_when=WHILE_ACTIVE)
    kind = b.CreatureSizeFact if case == "qualified_size" else b.CreatureTypeFact
    (fact,) = (f for f in comp.facts if _is(f, kind))
    return dataclasses.replace(
        comp,
        fact_qualifiers=(
            *comp.fact_qualifiers,
            FactQualifier(fact_key=b.fact_key(fact), applies_when=WHILE_ACTIVE),
        ),
    )


def _with_component(rep: Any, key: tuple[str, str], fn: Any) -> Any:
    return dataclasses.replace(
        rep,
        components=tuple(
            fn(x) if (x.record_key, x.semantic_key) == key else x
            for x in rep.components
        ),
    )


def _familiar_forms(rep: Any) -> dict[str, dict[str, Any]]:
    comps = {(x.record_key, x.semantic_key): x for x in rep.components}
    (source,) = (
        f for f in comps[b.FAMILIAR].facts if _is(f, b.SummonedCreatureTypeFact)
    )
    out = {}
    for ref in source.forms:
        comp = comps[(ref.record_key, ref.component_key)]
        sizes = [f for f in comp.facts if _is(f, b.CreatureSizeFact)]
        types = [f for f in comp.facts if _is(f, b.CreatureTypeFact)]
        out[ref.record_key] = {
            "applies_when_none": comp.applies_when is None,
            "no_options": comp.options == (),
            "size_and_type_unqualified": all(
                comp.qualifier_for(f) is None for f in (*sizes, *types)
            ),
            "one_direct_size": len(sizes) == 1,
            "one_direct_type_is_instead_of": [t.type for t in types]
            == [source.instead_of],
        }
    return out


def main() -> None:
    t0 = time.monotonic()
    preview = b.PREVIEW.read_bytes()
    out: dict[str, Any] = {
        "label": "SIMULATION - revalidation of the captured C8 native preview",
        "afterworlds_file": str(b.AFTERWORLDS_FILE),
        "validation_py_sha256": b.sha(VALIDATION.read_bytes()),
        "script_sha256": b.sha(Path(__file__).read_bytes()),
        "builder_sha256": b.sha(Path(b.__file__).read_bytes()),
        "builder_sha256_matches_report": b.sha(Path(b.__file__).read_bytes())
        == REPORT["builder_sha256"],
        "preview_sha256_matches_report": b.sha(preview) == REPORT["preview_sha256"],
        "proposals_match_report": {
            batch: b.sha((b.PREVIEW.parent / f"{batch}-C8-PROPOSAL.json").read_bytes())
            == v["rendered_proposal_sha256"]
            for batch, v in REPORT["batches"].items()
        },
        "schema_unchanged": [
            b.REPRESENTATION_SCHEMA_VERSION,
            b.representation_schema_hash(),
        ]
        == REPORT["schema"],
        "pins": all(b.sha(p.read_bytes()) == d for p, d in b.PINS.items()),
    }
    back = b.load_accepted_inputs(b.PREVIEW)
    assert b.serialize_accepted_inputs(back) == preview
    out["oracle_identity_matches_report"] = (
        b.oracle_identity(back.oracle) == REPORT["oracle_identity"]
    )
    lifted, _ = b.lift_accepted_inputs(
        b.load_accepted_inputs(b.SUCCESSOR), (b.SCHEMA_21_VERSION, b.SCHEMA_21_HASH)
    )
    nat = b.native(back, lifted)
    out["native"] = nat
    out["identities_match_report"] = all(
        nat[k] == REPORT["native"][k]
        for k in (
            "projection",
            "payload_hash",
            "successor_lifted_projection",
            "successor_lifted_payload_hash",
        )
    )
    rep = back.oracle.representation
    forms = _familiar_forms(rep)
    out["familiar_forms"] = forms
    out["familiar_forms_direct_unconditional"] = len(forms) == 11 and all(
        all(v.values()) for v in forms.values()
    )
    with c.private_store() as db:
        engine = b.create_engine(f"sqlite:///{db}")
        try:
            with b.create_session_factory(engine)() as s:
                binding = back.oracle.binding
                corpus = b.load_bound_corpus(
                    s, binding.package_uuid, binding.release_version
                )
                candidate = b.candidate_from_accepted_inputs(back)
                refused = {}
                for case in (
                    "option_arms",
                    "component_applies_when",
                    "qualified_type",
                    "qualified_size",
                ):
                    bad = dataclasses.replace(
                        candidate,
                        representation=_with_component(
                            candidate.representation,
                            CAT,
                            lambda x, case=case: _conditional(x, case),
                        ),
                    )
                    refused[case] = [
                        f for f in b.validate_candidate(bad, corpus) if NEEDLE in f
                    ][:2]
                out["conditional_variants_refused"] = refused
        finally:
            engine.dispose()
    out["seconds"] = round(time.monotonic() - t0)
    (b.HERE / "reports/c8-revalidation.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "native"}, indent=1))
    assert out["builder_sha256_matches_report"] and out["preview_sha256_matches_report"]
    assert all(out["proposals_match_report"].values()) and out["schema_unchanged"]
    assert out["pins"] and out["oracle_identity_matches_report"]
    assert out["identities_match_report"], nat
    assert not nat["validate_candidate_findings"], nat["validate_candidate_findings"]
    assert all(nat["malformed_variants_refused"].values())
    assert nat["own_gate_passed"] and nat["successor_refused_against_preview"]
    assert nat["preview_refused_against_successor"]
    assert nat["preview_reconstruction_clean"]
    assert nat["successor_lifted_reconstruction_clean"]
    assert out["familiar_forms_direct_unconditional"], forms
    assert all(refused.values()), refused
    print("REVALIDATION PASSED", out["seconds"], "s")


if __name__ == "__main__":
    main()
