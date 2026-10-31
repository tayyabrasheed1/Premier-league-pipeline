import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

st.set_page_config(page_title="Premier League Pipeline", layout="wide")


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


st.title("Premier League Data Pipeline")

# ---------- Sidebar: season ----------
seasons = query("select distinct season from marts.league_table order by season desc")[
    "season"
].tolist()

if not seasons:
    st.warning("No data yet. Run the pipeline and `dbt run` first.")
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

# ---------- 1. League table ----------
st.subheader("League table")
table = query(
    """
    select position, team_name as team, played as p, won as w, drawn as d, lost as l,
           goals_for as gf, goals_against as ga, goal_difference as gd, points as pts
    from marts.league_table
    where season = :season
    order by position
    """,
    {"season": season},
)
st.dataframe(table, hide_index=True)

# ---------- 2. Team view ----------
st.subheader("Team view")
teams = query(
    "select team_id, team_name from marts.league_table where season = :season order by team_name",
    {"season": season},
)
team_name = st.selectbox("Team", teams["team_name"])
team_id = int(teams.loc[teams["team_name"] == team_name, "team_id"].iloc[0])

results = query(
    """
    select f.kickoff_at::date as date,
           f.venue,
           o.team_name as opponent,
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
    st.markdown(f"**Form (latest first):** {' '.join(results['result'])}")
    st.dataframe(results, hide_index=True)

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
    st.bar_chart(ha.set_index("venue")["points_per_game"])

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
            "goals_for_rolling_5": "Goals for (5-match average)",
            "goals_against_rolling_5": "Goals against (5-match average)",
        }
    )
    st.line_chart(roll.set_index("kickoff_at"))
