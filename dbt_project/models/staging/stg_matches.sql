select
    match_id,
    season,
    matchday,
    utc_date            as kickoff_at,
    status,
    home_team_id,
    away_team_id,
    home_score,
    away_score,
    raw_json -> 'score' ->> 'winner' as winner,
    source_updated_at,
    loaded_at
from {{ source('raw', 'matches') }}
