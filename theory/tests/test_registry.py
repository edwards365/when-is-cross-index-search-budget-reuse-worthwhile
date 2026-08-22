import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_proof_registry_uses_declared_statuses_and_audits_proved_claims():
    registry = yaml.safe_load((ROOT / "theory" / "proof_status.yaml").read_text(encoding="utf-8"))
    allowed = set(registry["allowed_statuses"])
    assert allowed == {
        "imported_verified", "imported_unverified", "proved", "proof_sketch",
        "conjecture", "empirically_supported", "disproved", "blocked", "abandoned",
    }
    for claim in registry["claims"].values():
        assert claim["status"] in allowed
        if claim["status"] == "proved":
            assert claim["original_statement"]
            assert claim["dependencies"]
            assert claim["algorithm_relation"]
            assert claim["originality"]


def test_source_claim_map_has_required_fields_and_unique_ids():
    path = ROOT / "theory" / "source_claim_map.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "claim_id", "mathematical_claim", "original_source", "original_theorem_number",
        "required_assumptions", "original_checked", "directly_citable",
        "transferable_to_hnsw", "missing_transfer_conditions",
    }
    assert rows and set(rows[0]) == required
    assert len({row["claim_id"] for row in rows}) == len(rows)
    assert {row["original_checked"] for row in rows} <= {"true", "false"}
