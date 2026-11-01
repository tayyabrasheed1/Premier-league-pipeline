import os
from html import escape

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

st.set_page_config(page_title="Premier League Pipeline", layout="wide")

RESULT_COLOURS = {"W": "#13a538", "D": "#8c8c8c", "L": "#dc2626"}
RESULT_WORDS = {"W": "Won", "D": "Drawn", "L": "Lost"}
GOALS_FOR_COLOUR = "#13a538"
GOALS_AGAINST_COLOUR = "#dc2626"

# Colours are explicit or inherited, so the HTML reads well in light and dark themes.
CSS = """
<style>
.pl-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.pl-table th { text-align: center; font-weight: 600; font-size: 0.8rem; opacity: 0.7;
               padding: 8px 6px; border-bottom: 2px solid rgba(128,128,128,0.35); }
.pl-table td { text-align: center; padding: 7px 6px; border-bottom: 1px solid rgba(128,128,128,0.2); }
.pl-table th.club, .pl-table td.club { text-align: left; }
.pl-table td.pos { width: 2.5rem; font-weight: 600; border-left: 4px solid transparent; }
.pl-table tr.ucl td.pos { border-left-color: #2563eb; }
.pl-table tr.rel td.pos { border-left-color: #dc2626; }
.pl-table td.pts { font-weight: 700; }
.pl-table tbody tr:hover { background: rgba(128,128,128,0.08); }
.crest { width: 22px; height: 22px; object-fit: contain; vertical-align: middle; margin-right: 10px; }
.badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px;
         border-radius: 50%; color: #fff; font-size: 0.7rem; font-weight: 700; margin: 0 2px; }
.badge.big { width: 34px; height: 34px; font-size: 0.95rem; margin: 0 4px 0 0; }
.legend { font-size: 0.8rem; opacity: 0.8; margin-top: 8px; }
.legend span { display: inline-block; width: 10px; height: 10px; margin: 0 6px 0 14px; vertical-align: middle; }
.legend span:first-child { margin-left: 0; }
</style>
"""


@st.cache_resource
def get_engine():
    """One database connection pool, shared across reruns."""
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
    )
    return create_engine(url)


@st.cache_data(ttl=300)
def query(sql, params=None):
    """Run a SQL query and return a DataFrame. Results are cached for 5 minutes."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def season_label(season):
    return f"{season}/{str(season + 1)[-2:]}"


def crest(url):
    return f'<img class="crest" src="{escape(url)}" alt="">' if url else ""


def badge(result, tooltip="", big=False):
    size = " big" if big else ""
    return (
        f'<span class="badge{size}" style="background:{RESULT_COLOURS[result]}" '
        f'title="{escape(tooltip)}">{result}</span>'
    )


st.title("Premier League Data Pipeline")

# ---------- Sidebar: season ----------
try:
    seasons = query(
        "select distinct season from marts.league_table order by season desc"
    )["season"].tolist()
except Exception:
    seasons = []  # the marts don't exist until the DAG has run once

if not seasons:
    st.warning("No data yet. Trigger the premier_league_daily DAG in Airflow first.")
    st.stop()

season = int(st.sidebar.selectbox("Season", seasons, format_func=season_label))

# ---------- Top metrics: freshness ----------
progress = query(
    "select finished_matches, total_matches from core.dim_seasons where season = :season",
    {"season": season},
)
latest = query("select max(loaded_at) as last_change from raw.matches")

col1, col2 = st.columns(2)
if not progress.empty:
    col1.metric(
        "Matches finished",
        f"{int(progress['finished_matches'].iloc[0])} of {int(progress['total_matches'].iloc[0])}",
    )
last_change = latest["last_change"].iloc[0]
if pd.notna(last_change):
    col2.metric("Latest data change (database time)", last_change.strftime("%d %b %Y, %H:%M"))

# Last 5 results per team this season, oldest first, for the form badges.
recent = query(
    """
    select team_id, result, opponent, score, date
    from (
        select f.team_id, f.result, o.team_name as opponent,
               cast(f.goals_for as text) || '-' || cast(f.goals_against as text) as score,
               f.kickoff_at::date as date,
               f.kickoff_at,
               row_number() over (partition by f.team_id order by f.kickoff_at desc) as rn
        from core.fact_team_matches f
        left join core.dim_teams o on o.team_id = f.opponent_id
        where f.season = :season
    ) last_five
    where rn <= 5
    order by team_id, kickoff_at
    """,
    {"season": season},
)
form_html = {
    team_id: "".join(
        badge(r.result, f"{RESULT_WORDS[r.result]} {r.score} vs {r.opponent} ({r.date:%d %b})")
        for r in rows.itertuples()
    )
    for team_id, rows in recent.groupby("team_id")
}

# ---------- 1. League table ----------
st.subheader("League table")
table = query(
    """
    select l.position, l.team_id, l.team_name, t.crest_url, l.played, l.won, l.drawn, l.lost,
           l.goals_for, l.goals_against, l.goal_difference, l.points
    from marts.league_table l
    left join core.dim_teams t on t.team_id = l.team_id
    where l.season = :season
    order by l.position
    """,
    {"season": season},
)

team_count = len(table)
rows_html = []
for r in table.itertuples():
    zone = "ucl" if r.position <= 4 else "rel" if r.position > team_count - 3 else ""
    gd = f"+{r.goal_difference}" if r.goal_difference > 0 else str(r.goal_difference)
    rows_html.append(
        f'<tr class="{zone}"><td class="pos">{r.position}</td>'
        f'<td class="club">{crest(r.crest_url)}{escape(r.team_name)}</td>'
        f"<td>{r.played}</td><td>{r.won}</td><td>{r.drawn}</td><td>{r.lost}</td>"
        f"<td>{r.goals_for}</td><td>{r.goals_against}</td><td>{gd}</td>"
        f'<td class="pts">{r.points}</td><td>{form_html.get(r.team_id, "")}</td></tr>'
    )

st.html(
    CSS
    + '<table class="pl-table"><thead><tr><th>Pos</th><th class="club">Club</th>'
    "<th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th>"
    "<th>Pts</th><th>Last 5</th></tr></thead><tbody>"
    + "".join(rows_html)
    + "</tbody></table>"
    '<div class="legend"><span style="background:#2563eb"></span>Top 4'
    '<span style="background:#dc2626"></span>Relegation'
    "<span></span>Last 5 reads oldest to latest; hover a badge for the score</div>"
)

# ---------- 2. Team view ----------
st.subheader("Team view")
teams = table.sort_values("team_name")[["team_id", "team_name"]]
# Keep the chosen team across seasons; fall back to the leader if it wasn't in this one.
if st.session_state.get("team") not in teams["team_name"].tolist():
    st.session_state["team"] = table["team_name"].iloc[0]
team_name = st.selectbox("Team", teams["team_name"], key="team")
team_id = int(teams.loc[teams["team_name"] == team_name, "team_id"].iloc[0])

results = query(
    """
    select f.kickoff_at::date as date,
           f.venue,
           o.team_name as opponent,
           o.crest_url,
           cast(f.goals_for as text) || '-' || cast(f.goals_against as text) as score,
           f.result
    from core.fact_team_matches f
    left join core.dim_teams o on o.team_id = f.opponent_id
    where f.team_id = :team_id and f.season = :season
    order by f.kickoff_at desc
    limit 5
    """,
    {"team_id": team_id, "season": season},
)

if results.empty:
    st.info("No finished matches for this team in this season yet.")
else:
    badges = "".join(badge(r, big=True) for r in results["result"][::-1])
    result_rows = "".join(
        f"<tr><td>{r.date:%d %b %Y}</td><td>{'Home' if r.venue == 'HOME' else 'Away'}</td>"
        f'<td class="club">{crest(r.crest_url)}{escape(r.opponent)}</td>'
        f'<td class="pts">{r.score}</td><td>{badge(r.result, RESULT_WORDS[r.result])}</td></tr>'
        for r in results.itertuples()
    )
    st.html(
        CSS
        + f"<div><b>Form</b> <span style='opacity:0.7'>(oldest to latest)</span></div>"
        f"<div style='margin:8px 0 14px'>{badges}</div>"
        '<table class="pl-table"><thead><tr><th>Date</th><th>Venue</th>'
        '<th class="club">Opponent</th><th>Score</th><th>Result</th></tr></thead>'
        f"<tbody>{result_rows}</tbody></table>"
    )

# ---------- 3. Home vs away ----------
st.subheader("Home vs away points per game")
ha = query(
    """
    select venue, played, points_per_game
    from marts.home_vs_away_performance
    where season = :season and team_id = :team_id
    """,
    {"season": season, "team_id": team_id},
)
ha["points_per_game"] = ha["points_per_game"].astype(float)

metric_cols = st.columns(2)
for col, venue in zip(metric_cols, ["HOME", "AWAY"]):
    row = ha[ha["venue"] == venue]
    if not row.empty:
        col.metric(f"{venue.title()} points per game", f"{row['points_per_game'].iloc[0]:.2f}")
if not ha.empty:
    ha["venue"] = ha["venue"].str.title()
    st.bar_chart(ha.set_index("venue")["points_per_game"], horizontal=True, height=180)

# ---------- 4. Rolling goals ----------
st.subheader("Rolling 5-match goals")
roll = query(
    """
    select kickoff_at, goals_for_rolling_5, goals_against_rolling_5
    from marts.goals_for_against_rolling
    where team_id = :team_id and season = :season
    order by kickoff_at
    """,
    {"team_id": team_id, "season": season},
)
if not roll.empty:
    roll["goals_for_rolling_5"] = pd.to_numeric(roll["goals_for_rolling_5"])
    roll["goals_against_rolling_5"] = pd.to_numeric(roll["goals_against_rolling_5"])
    roll = roll.rename(
        columns={
            "goals_for_rolling_5": "Goals scored",
            "goals_against_rolling_5": "Goals conceded",
        }
    )
    st.caption("Average per match over the last 5 matches")
    st.line_chart(
        roll.set_index("kickoff_at")[["Goals scored", "Goals conceded"]],
        color=[GOALS_FOR_COLOUR, GOALS_AGAINST_COLOUR],
    )
