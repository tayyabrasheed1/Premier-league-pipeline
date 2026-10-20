select
    team_id,
    name        as team_name,
    short_name,
    tla,
    founded,
    venue
from {{ source('raw', 'teams') }}
