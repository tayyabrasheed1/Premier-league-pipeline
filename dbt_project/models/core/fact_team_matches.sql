with base as (
    select
        match_id, season, matchday, kickoff_at,
        home_team_id as team_id,
        away_team_id as opponent_id,
        'HOME'       as venue,
        home_score   as goals_for,
        away_score   as goals_against
    from {{ ref('fact_matches') }}
    where status = 'FINISHED'

    union all

    select
        match_id, season, matchday, kickoff_at,
        away_team_id as team_id,
        home_team_id as opponent_id,
        'AWAY'       as venue,
        away_score   as goals_for,
        home_score   as goals_against
    from {{ ref('fact_matches') }}
    where status = 'FINISHED'
)

select
    *,
    case
        when goals_for > goals_against then 'W'
        when goals_for = goals_against then 'D'
        else 'L'
    end as result,
    case
        when goals_for > goals_against then 3
        when goals_for = goals_against then 1
        else 0
    end as points
from base
