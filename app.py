import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta

# Load daily hitter file
url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
hitters_df = pd.read_csv(url)

# Get unique hitter list
unique_players = hitters_df[["player_name", "player_id", "team_id"]].drop_duplicates()
player_name = st.selectbox("Select a hitter:", unique_players["player_name"].unique())

# Get ID and team for selected hitter
selected_row = unique_players[unique_players["player_name"] == player_name].iloc[0]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]

# Map team_id to full team name
team_id_map = {
    109: "Arizona Diamondbacks",
    144: "Atlanta Braves",
    110: "Baltimore Orioles",
    111: "Boston Red Sox",
    112: "Chicago Cubs",
    145: "Chicago White Sox",
    113: "Cincinnati Reds",
    114: "Cleveland Guardians",
    115: "Colorado Rockies",
    116: "Detroit Tigers",
    117: "Houston Astros",
    118: "Kansas City Royals",
    119: "Los Angeles Angels",
    137: "Los Angeles Dodgers",
    146: "Miami Marlins",
    158: "Milwaukee Brewers",
    121: "Minnesota Twins",
    135: "New York Mets",
    147: "New York Yankees",
    133: "Oakland Athletics",
    134: "Philadelphia Phillies",
    143: "Pittsburgh Pirates",
    142: "San Diego Padres",
    138: "San Francisco Giants",
    139: "Seattle Mariners",
    140: "St. Louis Cardinals",
    141: "Tampa Bay Rays",
    120: "Washington Nationals",
    136: "Toronto Blue Jays"
}
batter_team_name = team_id_map.get(team_id, None)

# Load pitcher data
pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

# Try to find opposing pitcher using team name
pitcher_row = pitchers_df[pitchers_df["Opponent"] == batter_team_name]
pitcher_name = None
pitcher_id = None

if not pitcher_row.empty:
    pitcher_name = pitcher_row.iloc[0]["Pitcher Name"]
    st.write(f"🧱 Probable Pitcher: {pitcher_name}")
else:
    st.warning("❗ No probable pitcher found for this matchup.")

# Get pitcher Statcast data
if pitcher_name:
    try:
        pitcher_id = int(pitcher_row.iloc[0]["MLB ID"])
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
        df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)

        if not df_pitcher.empty:
            avg_ev_allowed = df_pitcher['launch_speed'].mean()
            hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
            total_contact = df_pitcher.shape[0]
            hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
            xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

            # Add indicators
            xba_tag = "✅" if xba_allowed > 0.280 else "⚠️"
            hard_hit_tag = "✅" if hard_hit_pct_allowed > 35 else "⚠️"
            ev_tag = "✅" if avg_ev_allowed > 89 else "⚠️"

            st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed} {xba_tag}")
            st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}% {hard_hit_tag}")
            st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph {ev_tag}")

            score = 50
            if xba_allowed > 0.280: score += 10
            if hard_hit_pct_allowed > 40: score += 10
            if avg_ev_allowed > 89: score += 5
        else:
            st.warning("No recent data for pitcher.")
    except:
        st.warning("Pitcher lookup failed. Check spelling.")

# Get batter Statcast data
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')

st.write(f"📅 Date range: {start_date} → {end_date}")

df = statcast_batter(start_date, end_date, batter_id)

if not df.empty:
    avg_exit_velo = df['launch_speed'].mean()
    hard_hits = df[df['launch_speed'] >= 95].shape[0]
    total_batted_balls = df.shape[0]
    hard_hit_pct = round((hard_hits / total_batted_balls) * 100, 2) if total_batted_balls else 0
    xba = round(df['estimated_ba_using_speedangle'].mean(), 3)

    # Load hitter daily stat file for visual summary
    daily_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
    full_df = pd.read_csv(daily_url)
    recent_df = full_df[(full_df["player_id"] == batter_id) & (full_df["game_date"] >= start_date)]

    total_abs = recent_df["at_bats"].sum()
    total_hits = recent_df["hits"].sum()
    total_rbis = recent_df["rbi"].sum()
    total_hrs = recent_df["home_runs"].sum()
    total_bases = (recent_df["hits"] + 2 * recent_df["home_runs"]).sum()  # crude approx

    max_hits = recent_df["hits"].max()
    max_rbis = recent_df["rbi"].max()
    max_bases = (recent_df["hits"] + 2 * recent_df["home_runs"]).max()  # crude again

    avg = round(recent_df["avg"].mean(), 3)
    obp = round(recent_df["obp"].mean(), 3)
    slg = round(recent_df["slg"].mean(), 3)

    # Totals Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ABs", total_abs)
    col2.metric("Hits", f"{total_hits}", f"Max: {max_hits}")
    col3.metric("Total Bases", f"{total_bases}", f"Max: {max_bases}")
    col4.metric("RBIs", f"{total_rbis}", f"Max: {max_rbis}")
    col5.metric("HRs", total_hrs)

    # Averages Row
    col1, col2, col3 = st.columns(3)
    col1.metric("AVG", f"{avg}")
    col2.metric("OBP", f"{obp}")
    col3.metric("SLG", f"{slg}")

    # Rest of Statcast
    st.write(f"**Average Exit Velocity:** {round(avg_exit_velo, 1)} mph")
    st.write(f"**Hard Hit %:** {hard_hit_pct}%")
    st.write(f"**xBA (Expected BA):** {xba}")

    if 'score' not in locals():
        score = 50

    if xba > 0.300: score += 15
    if hard_hit_pct > 45: score += 15
    if avg_exit_velo > 91: score += 10

    st.write(f"🧠 **Cycle Score**: {score}/100")
    if score >= 85:
        st.success("🔥 LOCK")
    elif score >= 70:
        st.info("✅ Lean")
    else:
        st.warning("⚠️ Fade")
else:
    st.warning("No Statcast data found for this timeframe.")
