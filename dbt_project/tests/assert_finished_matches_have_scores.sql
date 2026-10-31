select match_id, status, home_score, away_score
from {{ ref('fact_matches') }}
where status = 'FINISHED'
  and (home_score is null or away_score is null)
