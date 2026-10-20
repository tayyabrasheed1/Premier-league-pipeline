select
    f.season,
    f.team_id,
    t.team_name,
    f.match_id,
    f.matchday,
    f.kickoff_at,
    f.venue,
    f.goals_for,
    f.goals_against,
    round(avg(f.goals_for) over (
        partition by f.team_id
        order by f.kickoff_at
        rows between 4 preceding and current row
    ), 2) as goals_for_rolling_5,
    round(avg(f.goals_against) over (
        partition by f.team_id
        order by f.kickoff_at
        rows between 4 preceding and current row
    ), 2) as goals_against_rolling_5
from {{ ref('fact_team_matches') }} f
left join {{ ref('dim_teams') }} t on t.team_id = f.team_id
