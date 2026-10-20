import argparse
import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

load_dotenv()

RAW_DIR = Path("data/raw")

UPSERT_MATCH = """
INSERT INTO raw.matches (
    match_id, season, utc_date, status, matchday,
    home_team_id, away_team_id, home_score, away_score,
    source_updated_at, raw_json
)
VALUES (
    %(match_id)s, %(season)s, %(utc_date)s, %(status)s, %(matchday)s,
    %(home_team_id)s, %(away_team_id)s, %(home_score)s, %(away_score)s,
    %(source_updated_at)s, %(raw_json)s
)
ON CONFLICT (match_id) DO UPDATE SET
    season            = EXCLUDED.season,
    utc_date          = EXCLUDED.utc_date,
    status            = EXCLUDED.status,
    matchday          = EXCLUDED.matchday,
    home_team_id      = EXCLUDED.home_team_id,
    away_team_id      = EXCLUDED.away_team_id,
    home_score        = EXCLUDED.home_score,
    away_score        = EXCLUDED.away_score,
    source_updated_at = EXCLUDED.source_updated_at,
    raw_json          = EXCLUDED.raw_json,
    loaded_at         = now()
WHERE raw.matches.raw_json IS DISTINCT FROM EXCLUDED.raw_json;
"""

UPSERT_TEAM = """
INSERT INTO raw.teams (team_id, name, short_name, tla, founded, venue, raw_json)
VALUES (
    %(team_id)s, %(name)s, %(short_name)s, %(tla)s,
    %(founded)s, %(venue)s, %(raw_json)s
)
ON CONFLICT (team_id) DO UPDATE SET
    name       = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    tla        = EXCLUDED.tla,
    founded    = EXCLUDED.founded,
    venue      = EXCLUDED.venue,
    raw_json   = EXCLUDED.raw_json,
    loaded_at  = now()
WHERE raw.teams.raw_json IS DISTINCT FROM EXCLUDED.raw_json;
"""


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def latest_file(kind, season):
    """Return the newest raw JSON file for matches or teams."""
    folder = RAW_DIR / kind / f"season={season}"
    files = sorted(folder.rglob("*.json"))
    if not files:
        raise SystemExit(f"No raw files found in {folder}. Run fetch_matches.py first.")
    return files[-1]


def parse_match(m):
    full_time = m["score"]["fullTime"]
    return {
        "match_id": m["id"],
        "season": int(m["season"]["startDate"][:4]),
        "utc_date": m["utcDate"],
        "status": m["status"],
        "matchday": m.get("matchday"),
        "home_team_id": m["homeTeam"]["id"],
        "away_team_id": m["awayTeam"]["id"],
        "home_score": full_time["home"],
        "away_score": full_time["away"],
        "source_updated_at": m["lastUpdated"],
        "raw_json": Json(m),
    }


def parse_team(t):
    return {
        "team_id": t["id"],
        "name": t.get("name"),
        "short_name": t.get("shortName"),
        "tla": t.get("tla"),
        "founded": t.get("founded"),
        "venue": t.get("venue"),
        "raw_json": Json(t),
    }


def load_file(conn, path, key, sql, parser):
    """Upsert every record in a raw file. Return (total, changed)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    changed = 0
    with conn.cursor() as cur:
        for record in data[key]:
            cur.execute(sql, parser(record))
            changed += cur.rowcount  # 1 if inserted or updated, 0 if skipped
    conn.commit()
    return len(data[key]), changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    args = parser.parse_args()

    conn = get_connection()
    try:
        path = latest_file("teams", args.season)
        total, changed = load_file(conn, path, "teams", UPSERT_TEAM, parse_team)
        print(f"teams:   {total} in file, {changed} inserted or updated ({path.name})")

        path = latest_file("matches", args.season)
        total, changed = load_file(conn, path, "matches", UPSERT_MATCH, parse_match)
        print(f"matches: {total} in file, {changed} inserted or updated ({path.name})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
