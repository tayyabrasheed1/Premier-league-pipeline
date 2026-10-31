select
    team_id,
    name        as team_name,
    short_name,
    tla,
    founded,
    venue,
    raw_json ->> 'crest' as crest_url
from {{ source('raw', 'teams') }}
