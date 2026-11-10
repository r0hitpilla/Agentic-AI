"""Tests for the reference engine, knowledge files, schemas and examples.

Run from the repo root:  python3 -m pytest -q
"""
import json
import pathlib
import subprocess
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import Classifier  # noqa: E402

CLF = Classifier()
SCENARIOS = yaml.safe_load((ROOT / "knowledge" / "scenarios.yaml").read_text())
CASES = yaml.safe_load((ROOT / "tests" / "scenario_cases.yaml").read_text())["cases"]
SCENARIO_IDS = {s["id"] for s in SCENARIOS["scenarios"]}


# ------------------------------------------------------------------ scenarios
@pytest.mark.parametrize("sid", sorted(CASES))
def test_scenario_case(sid):
    assert sid in SCENARIO_IDS, f"{sid} has a test case but no scenario"
    case = CASES[sid]
    expect = case["expect"]
    got = {}
    if "evidence" in case:
        got.update(CLF.classify(case["evidence"]))
    if "merge" in case:
        got["merge"] = CLF.merge_decision(case["merge"]["rank"], case["merge"].get("same_environment", True))
    if "span" in case:
        got["span"] = CLF.span_decision(case["span"]).value
    if "drift" in case:
        got["drift"] = CLF.drift(case["drift"]["previous"], case["drift"]["current"])
    if "source_of_truth" in case:
        got["source_of_truth"] = CLF.source_of_truth(case["source_of_truth"])
    for key, want in expect.items():
        assert got.get(key) == want, f"{sid}: {key} expected {want!r}, got {got.get(key)!r} (rules {got.get('rules')})"


def test_scenarios_well_formed():
    ids = [s["id"] for s in SCENARIOS["scenarios"]]
    assert len(ids) == len(set(ids))
    groups = {g["id"] for g in SCENARIOS["groups"]}
    required = {"id", "group", "title", "situation", "signals", "record_as", "expected", "action"}
    for s in SCENARIOS["scenarios"]:
        assert required <= set(s), s["id"]
        assert s["group"] in groups and s["id"].startswith(f"SC-{s['group']}")


def test_classification_scenarios_have_record_type_consistent_with_cases():
    by_id = {s["id"]: s for s in SCENARIOS["scenarios"]}
    for sid, case in CASES.items():
        rt = case["expect"].get("record_type")
        if rt:
            assert by_id[sid]["record_as"] == rt, f"{sid}: scenario says {by_id[sid]['record_as']}, case says {rt}"


def test_scenario_doc_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "render_scenarios.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ------------------------------------------------------------------ knowledge
@pytest.mark.parametrize("path", sorted((ROOT / "knowledge").glob("*.yaml")), ids=lambda p: p.name)
def test_knowledge_yaml_parses(path):
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict) and data.get("version") == 1


def test_risk_tiers_cover_range():
    tiers = CLF.risk["tiers"]
    assert [t["tier"] for t in tiers] == ["low", "medium", "high", "critical"]
    assert tiers[-1]["below"] > 100


# ------------------------------------------------------------ schemas/examples
jsonschema = pytest.importorskip("jsonschema")


def _validator(name):
    schema = json.loads((ROOT / "schemas" / name).read_text())
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


@pytest.mark.parametrize("example", sorted((ROOT / "examples").glob("*.yaml")), ids=lambda p: p.name)
def test_examples_validate(example):
    data = yaml.safe_load(example.read_text())
    schema = data.pop("$schema_name", "agent-record.schema.json") if isinstance(data, dict) else None
    errors = list(_validator(schema).iter_errors(data))
    assert not errors, [e.message for e in errors]


def test_managed_record_requires_owner_identity_gateway():
    v = _validator("agent-record.schema.json")
    shadow = yaml.safe_load((ROOT / "examples" / "shadow-loan-agent.yaml").read_text())
    shadow["classification"]["managed_status"] = "managed"
    assert list(v.iter_errors(shadow)), "managed record without governance must fail"


def test_kyc_example_risk_matches_engine():
    kyc = yaml.safe_load((ROOT / "examples" / "kyc-onboarding-agent.yaml").read_text())
    r = CLF.risk_score({
        "capabilities": ["customer_record_change"],
        "exposure": ["customer_facing"],
        "data": ["account"],
        "controls": list(CLF.risk["control_coverage"]["credits"]),
    }, kyc["classification"]["managed_status"], kyc["classification"]["identity_level"])
    assert r["score"] == kyc["risk"]["score"]
    assert r["tier"] == kyc["risk"]["tier"] == kyc["governance"]["risk_tier"]


def test_shadow_example_risk_and_confidence_match_engine():
    sh = yaml.safe_load((ROOT / "examples" / "shadow-loan-agent.yaml").read_text())
    r = CLF.risk_score({"capabilities": ["read_only"], "exposure": ["email_web_or_ticket_input"], "data": ["credit"]},
                       sh["classification"]["managed_status"], sh["classification"]["identity_level"])
    assert (r["score"], r["tier"]) == (sh["risk"]["score"], sh["risk"]["tier"])
    assert CLF.confidence(sh["classification"]["evidence_planes"]) == sh["classification"]["confidence"]


def test_openapi_spec_valid():
    osv = pytest.importorskip("openapi_spec_validator")
    from openapi_spec_validator.readers import read_from_filename
    path = ROOT / "api" / "inventory-api.openapi.yaml"
    spec, _ = read_from_filename(str(path))
    osv.validate(spec, base_uri=path.resolve().as_uri())


def test_business_keys_never_store_has_no_stitch_confidence():
    keys = yaml.safe_load((ROOT / "knowledge" / "business-keys.yaml").read_text())["keys"]
    for k in keys:
        assert k["handling"] in {"tokenise", "never_store", "plain"}
        if k["handling"] == "never_store":
            assert "stitch_confidence" not in k, f"{k['id']} must not be used for stitching"
