select
    f.season,
    f.team_id,
    t.team_name,
    f.venue,
    count(*)                    as played,
    sum(f.points)               as points,
    round(avg(f.points), 2)     as points_per_game,
    sum(f.goals_for)            as goals_for,
    sum(f.goals_against)        as goals_against
from {{ ref('fact_team_matches') }} f
left join {{ ref('dim_teams') }} t on t.team_id = f.team_id
group by f.season, f.team_id, t.team_name, f.venue
