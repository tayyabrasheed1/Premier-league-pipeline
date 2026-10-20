with ranked as (
    select
        f.*,
        row_number() over (partition by team_id order by kickoff_at desc) as recency
    from {{ ref('fact_team_matches') }} f
)

select
    r.team_id,
    t.team_name,
    count(*)        as matches_counted,
    sum(r.points)   as points_last_5,
    string_agg(r.result, '' order by r.kickoff_at desc) as form_latest_first,
    sum(r.goals_for)     as goals_for,
    sum(r.goals_against) as goals_against
from ranked r
left join {{ ref('dim_teams') }} t on t.team_id = r.team_id
where r.recency <= 5
group by r.team_id, t.team_name
