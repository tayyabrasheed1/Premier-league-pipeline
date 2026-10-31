select
    team_id,
    team_name,
    short_name,
    tla,
    founded,
    venue,
    crest_url
from {{ ref('stg_teams') }}
