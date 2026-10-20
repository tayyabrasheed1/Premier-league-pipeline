select
    f.season,
    rank() over (
        partition by f.season
        order by sum(f.points) desc,
                 sum(f.goals_for) - sum(f.goals_against) desc,
                 sum(f.goals_for) desc
    ) as position,
    f.team_id,
    t.team_name,
    count(*)                                  as played,
    count(*) filter (where f.result = 'W')    as won,
    count(*) filter (where f.result = 'D')    as drawn,
    count(*) filter (where f.result = 'L')    as lost,
    sum(f.goals_for)                          as goals_for,
    sum(f.goals_against)                      as goals_against,
    sum(f.goals_for) - sum(f.goals_against)   as goal_difference,
    sum(f.points)                             as points
from {{ ref('fact_team_matches') }} f
left join {{ ref('dim_teams') }} t on t.team_id = f.team_id
group by f.season, f.team_id, t.team_name
