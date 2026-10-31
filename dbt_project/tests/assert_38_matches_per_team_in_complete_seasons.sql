with complete_seasons as (
    select season
    from {{ ref('dim_seasons') }}
    where finished_matches = 380   -- 20 teams x 19 home matches
)

select f.season, f.team_id, count(*) as matches_played
from {{ ref('fact_team_matches') }} f
join complete_seasons c on c.season = f.season
group by f.season, f.team_id
having count(*) <> 38
