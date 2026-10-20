select
    team_id,
    team_name,
    short_name,
    tla,
    founded,
    venue
from {{ ref('stg_teams') }}
