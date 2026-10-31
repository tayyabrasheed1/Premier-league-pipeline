import json

from ingest.load_matches import UPSERT_MATCH, load_file, parse_match


def make_match(
    match_id,
    status="FINISHED",
    home=1,
    away=0,
    last_updated="2025-08-16T18:00:00Z",
    utc_date="2025-08-16T15:00:00Z",
):
    """Return a fake match shaped like the API response."""
    return {
        "id": match_id,
        "season": {"startDate": "2025-08-01"},
        "utcDate": utc_date,
        "status": status,
        "matchday": 1,
        "homeTeam": {"id": 57},
        "awayTeam": {"id": 61},
        "score": {"winner": None, "fullTime": {"home": home, "away": away}},
        "lastUpdated": last_updated,
    }


def write_raw(tmp_path, name, matches):
    path = tmp_path / name
    path.write_text(json.dumps({"matches": matches}), encoding="utf-8")
    return path


def load(conn, path):
    """Load a raw file and return the number of inserted or updated rows."""
    _, changed = load_file(conn, path, "matches", UPSERT_MATCH, parse_match)
    return changed


def rows(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT match_id, status, home_score, away_score, "
            "source_updated_at, loaded_at FROM raw.matches ORDER BY match_id"
        )
        return cur.fetchall()


def test_loading_twice_changes_nothing(conn, tmp_path):
    path = write_raw(tmp_path, "m.json", [make_match(1), make_match(2), make_match(3)])

    assert load(conn, path) == 3
    before = rows(conn)

    assert load(conn, path) == 0
    assert rows(conn) == before


def test_changed_score_updates_only_that_row(conn, tmp_path):
    v1 = [make_match(1), make_match(2), make_match(3)]
    load(conn, write_raw(tmp_path, "v1.json", v1))
    before = {row[0]: row for row in rows(conn)}

    v2 = [
        make_match(1),
        make_match(2, home=3, away=1, last_updated="2025-08-17T09:00:00Z"),
        make_match(3),
    ]
    assert load(conn, write_raw(tmp_path, "v2.json", v2)) == 1

    after = {row[0]: row for row in rows(conn)}
    assert len(after) == 3
    assert after[2][2:4] == (3, 1)
    assert after[1] == before[1]
    assert after[3] == before[3]
    assert after[2][5] > before[2][5]


def test_postponed_match_updates_in_place(conn, tmp_path):
    scheduled = make_match(10, status="SCHEDULED", home=None, away=None)
    load(conn, write_raw(tmp_path, "a.json", [scheduled]))

    postponed = make_match(
        10,
        status="POSTPONED",
        home=None,
        away=None,
        last_updated="2025-08-15T10:00:00Z",
    )
    assert load(conn, write_raw(tmp_path, "b.json", [postponed])) == 1

    result = rows(conn)
    assert len(result) == 1
    assert result[0][1] == "POSTPONED"
