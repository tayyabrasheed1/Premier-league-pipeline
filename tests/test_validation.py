import copy
import json

import pytest

from ingest.load_matches import UPSERT_MATCH, load_file, parse_match
from ingest.validate import SchemaError, validate_matches

GOOD = {
    "id": 1,
    "season": {"startDate": "2025-08-01"},
    "utcDate": "2025-08-16T15:00:00Z",
    "status": "FINISHED",
    "matchday": 1,
    "homeTeam": {"id": 57},
    "awayTeam": {"id": 61},
    "score": {"winner": "HOME_TEAM", "fullTime": {"home": 2, "away": 0}},
    "lastUpdated": "2025-08-16T18:00:00Z",
}


def renamed_field():
    record = copy.deepcopy(GOOD)
    record["match_id"] = record.pop("id")
    return record


def wrong_type():
    record = copy.deepcopy(GOOD)
    record["score"]["fullTime"]["home"] = [2]   # a number became a list
    return record


def test_valid_records_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    validate_matches([GOOD], "matches.json")


def test_extra_field_is_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    record = copy.deepcopy(GOOD)
    record["brandNewField"] = "hello"
    validate_matches([record], "matches.json")


def test_renamed_field_is_quarantined(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SchemaError):
        validate_matches([GOOD, renamed_field()], "matches.json")
    assert len(list((tmp_path / "data" / "quarantine").glob("*.json"))) == 1


def test_wrong_type_is_quarantined(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SchemaError):
        validate_matches([wrong_type()], "matches.json")


def test_loader_refuses_broken_file_and_writes_nothing(conn, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "matches.json"
    path.write_text(json.dumps({"matches": [GOOD, renamed_field()]}))

    with pytest.raises(SchemaError):
        load_file(conn, path, "matches", UPSERT_MATCH, parse_match, validator=validate_matches)

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw.matches")
        assert cur.fetchone()[0] == 0   # even the good record was not loaded
