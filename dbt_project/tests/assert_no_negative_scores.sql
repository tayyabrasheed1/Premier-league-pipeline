select match_id, home_score, away_score
from {{ ref('fact_matches') }}
where home_score < 0 or away_score < 0
