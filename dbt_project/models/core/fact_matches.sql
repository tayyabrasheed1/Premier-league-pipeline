select
    match_id,
    season,
    matchday,
    kickoff_at,
    status,
    home_team_id,
    away_team_id,
    home_score,
    away_score,
    case
        when home_score > away_score then 'HOME'
        when away_score > home_score then 'AWAY'
        when home_score = away_score then 'DRAW'
    end as result,
    source_updated_at
from {{ ref('stg_matches') }}
