CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.matches (
    match_id          BIGINT PRIMARY KEY,
    season            INT NOT NULL,
    utc_date          TIMESTAMPTZ,
    status            TEXT,
    matchday          INT,
    home_team_id      BIGINT,
    away_team_id      BIGINT,
    home_score        INT,
    away_score        INT,
    source_updated_at TIMESTAMPTZ,
    loaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_json          JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.teams (
    team_id    BIGINT PRIMARY KEY,
    name       TEXT,
    short_name TEXT,
    tla        TEXT,
    founded    INT,
    venue      TEXT,
    loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_json   JSONB NOT NULL
);
