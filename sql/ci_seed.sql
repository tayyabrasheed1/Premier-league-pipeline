INSERT INTO raw.teams (team_id, name, short_name, tla, founded, venue, raw_json) VALUES
(1, 'Team A FC', 'Team A', 'TMA', 1900, 'A Park', '{}'),
(2, 'Team B FC', 'Team B', 'TMB', 1901, 'B Park', '{}'),
(3, 'Team C FC', 'Team C', 'TMC', 1902, 'C Park', '{}'),
(4, 'Team D FC', 'Team D', 'TMD', 1903, 'D Park', '{}');

INSERT INTO raw.matches (
    match_id, season, utc_date, status, matchday, home_team_id, away_team_id,
    home_score, away_score, source_updated_at, raw_json
) VALUES
(1, 2025, '2025-08-16 15:00+00', 'FINISHED', 1, 1, 2, 2, 0, '2025-08-16 17:00+00', '{"score":{"winner":"HOME_TEAM"}}'),
(2, 2025, '2025-08-16 15:00+00', 'FINISHED', 1, 3, 4, 1, 1, '2025-08-16 17:00+00', '{"score":{"winner":"DRAW"}}'),
(3, 2025, '2025-08-23 15:00+00', 'FINISHED', 2, 1, 3, 0, 1, '2025-08-23 17:00+00', '{"score":{"winner":"AWAY_TEAM"}}'),
(4, 2025, '2025-08-23 15:00+00', 'FINISHED', 2, 4, 2, 3, 2, '2025-08-23 17:00+00', '{"score":{"winner":"HOME_TEAM"}}'),
(5, 2025, '2025-08-30 15:00+00', 'FINISHED', 3, 1, 4, 2, 2, '2025-08-30 17:00+00', '{"score":{"winner":"DRAW"}}'),
(6, 2025, '2025-08-30 15:00+00', 'FINISHED', 3, 2, 3, 0, 0, '2025-08-30 17:00+00', '{"score":{"winner":"DRAW"}}'),
(7, 2025, '2025-09-13 15:00+00', 'SCHEDULED', 4, 2, 1, NULL, NULL, '2025-08-30 17:00+00', '{"score":{"winner":null}}');
