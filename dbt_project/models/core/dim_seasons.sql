select
    season,
    min(kickoff_at)                          as first_match_at,
    max(kickoff_at)                          as last_match_at,
    count(*)                                 as total_matches,
    count(*) filter (where status = 'FINISHED') as finished_matches
from {{ ref('stg_matches') }}
group by season
