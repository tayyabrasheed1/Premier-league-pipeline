import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

QUARANTINE_DIR = Path("data/quarantine")


class SchemaError(Exception):
    """Raised when the API response no longer matches the shape we expect."""


class FullTime(BaseModel):
    home: int | None   # required, but may be null (match not played yet)
    away: int | None


class Score(BaseModel):
    fullTime: FullTime


class TeamRef(BaseModel):
    id: int


class Season(BaseModel):
    startDate: str


class Match(BaseModel):
    id: int
    utcDate: str
    status: str
    matchday: int | None
    homeTeam: TeamRef
    awayTeam: TeamRef
    score: Score
    lastUpdated: str
    season: Season


def validate_matches(records, source_path):
    """Check every match. If any are bad, quarantine them and stop."""
    bad = []
    for record in records:
        try:
            Match.model_validate(record)
        except ValidationError as error:
            bad.append({"record": record, "error": str(error)})

    if bad:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        out = QUARANTINE_DIR / f"matches_{datetime.now():%Y%m%dT%H%M%S}.json"
        out.write_text(json.dumps(bad, indent=2))
        raise SchemaError(
            f"{len(bad)} of {len(records)} records in {source_path} failed validation. "
            f"Quarantined to {out}. First error: {bad[0]['error']}"
        )
