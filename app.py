import streamlit as st
import pandas as pd
from pybaseball import statcast_pitcher, statcast_batter
from datetime import datetime, timedelta

# Load hitter data
hitters_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
hitters_df = pd.read_csv(hitters_url)

# Hitter selection
unique_players = hitters_df[["player_name", "player_id", "team_id"]].drop_duplicates()
player_name = st.selectbox("Select a hitter:", unique_players["player_name"].unique())

# Player info
selected_row = unique_players[unique_players["player_name"] == player_name].iloc[0]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]

# Team ID map
team_id_map = {
    109: "Arizona Diamondbacks", 144: "Atlanta Braves", 110: "Baltimore Orioles", 111: "Boston Red Sox",
    112: "Chicago Cubs", 145: "Chicago White Sox", 113: "Cincinnati Reds", 114: "Cleveland Guardians",
    115: "Colorado Rockies", 116: "Detroit Tigers", 117: "Houston Astros", 118: "Kansas City Royals",
    119: "Los Angeles Angels", 137: "Los Angeles Dodgers", 146: "Miami Marlins", 158: "Milwaukee Brewers",
    121: "Minnesota Twins", 135: "New York Mets", 147: "New York Yankees", 133: "Oakland Athletics",
    134: "Philadelphia Phillies", 143: "Pittsburgh Pirates", 142: "San Diego Padres", 138: "San Francisco Giants",
    139: "Seattle Mariners", 140: "St. Louis Cardinals", 141: "Tampa Bay Rays", 120: "Texas Rangers",
    136: "Toronto Blue Jays", 150: "Washington Nationals"
}
batter_team_name = team_id_map.get(team_id, None)

# Load pitcher data
pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

# ✅ This is the line that worked
pitcher_row = pitchers_df[pitchers_df["Opponent"] == batter_team_name]

pitcher_name = None
pitcher_id = None

# Layout row 1
col1, col2 = st.columns([1, 2])
with col1:
    st.image(f"https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{batter_id}/headshot/67/current.png", width=120)
    if not pitcher_row.empty:
        pitcher_name = pitcher_row.iloc[0]["Pitcher Name"]
        st.write(f"🧱 **Probable Pitcher:** {pitcher_name}")
    else:
        st.warning("❗ No probable pitcher found.")

with col2:
    if pitcher_name:
        try:
            pitcher_id = int(pitcher_row.iloc[0]["MLB ID"])
            start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
            end_date = datetime.today().strftime('%Y-%m-%d')
            df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)

            if not df_pitcher.empty:
                avg_ev_allowed = df_pitcher['launch_speed'].mean()
                hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
                total_contact = df_pitcher.shape[0]
                hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
                xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

                st.subheader("🎯 Pitcher Statcast (14 days)")
                st.write(f"xBA Allowed: {xba_allowed} {'🟢' if xba_allowed > 0.280 else '🔴'}")
                st.write(f"Hard Hit % Allowed: {hard_hit_pct_allowed}% {'🟢' if hard_hit_pct_allowed > 35 else '🔴'}")
                st.write(f"Avg Exit Velo Allowed: {round(avg_ev_allowed, 1)} mph {'🟢' if avg_ev_allowed > 88 else '🔴'}")

                score = 50
                if xba_allowed > 0.280: score += 10
                if hard_hit_pct_allowed > 40: score += 10
                if avg_ev_allowed > 89: score += 5
            else:
                st.warning("No recent Statcast data for pitcher.")
        except:
            st.warning("Pitcher lookup failed.")

# Get last 10 games
player_games = hitters_df[hitters_df["player_id"] == batter_id].sort_values("game_date", ascending=False).head(10)
player_games["TB"] = player_games["hits"] + player_games["home_runs"]  # crude calc

# Layout row 2
col3, col4 = st.columns(2)

if not player_games.empty:
    total_ab = player_games["at_bats"].sum()
    total_hits = player_games["hits"].sum()
    total_hr = player_games["home_runs"].sum()
    total_rbi = player_games["rbi"].sum()
    total_bb = player_games["base_on_balls"].sum()
    total_tb = player_games["TB"].sum()
    total_runs = player_games["rbi"].sum()  # Replace if you add runs column

    slg = round(total_tb / total_ab, 3) if total_ab else 0
    avg = round(total_hits / total_ab, 3) if total_ab else 0

    max_hits = player_games["hits"].max()
    max_tb = player_games["TB"].max()
    max_rbi = player_games["rbi"].max()
    max_runs = player_games["rbi"].max()  # Replace if you add runs column

    with col3:
        st.subheader("📊 Last 10 Games (Totals)")
        st.write(f"**At-Bats (AB):** {total_ab}")
        st.write(f"**Hits (H):** {total_hits}")
        st.write(f"**AVG:** {avg}")
        st.write(f"**Total Bases (TB):** {total_tb}")
        st.write(f"**Home Runs (HR):** {total_hr}")
        st.write(f"**RBIs:** {total_rbi}")
        st.write(f"**Walks (BB):** {total_bb}")
        st.write(f"**SLG:** {slg}")

    with col4:
        st.subheader("🎯 Max in a Game")
        st.write(f"**Max Hits:** {max_hits}")
        st.write(f"**Max TB:** {max_tb}")
        st.write(f"**Max RBI:** {max_rbi}")
        st.write(f"**Max Runs:** {max_runs}")
else:
    st.warning("No recent game log data found.")

# Statcast for hitter
try:
    start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    df_batter = statcast_batter(start_date, end_date, batter_id)

    if not df_batter.empty:
        avg_ev = df_batter['launch_speed'].mean()
        hard_hits = df_batter[df_batter['launch_speed'] >= 95].shape[0]
        total_batted_balls = df_batter.shape[0]
        hard_hit_pct = round((hard_hits / total_batted_balls) * 100, 2) if total_batted_balls else 0
        xba = round(df_batter['estimated_ba_using_speedangle'].mean(), 3)

        st.subheader("💥 Batter Statcast (14 days)")
        st.write(f"**Avg Exit Velo:** {round(avg_ev, 1)} mph")
        st.write(f"**Hard Hit %:** {hard_hit_pct}%")
        st.write(f"**xBA (Expected BA):** {xba}")

        if 'score' not in locals():
            score = 50

        if xba > 0.300: score += 15
        if hard_hit_pct > 45: score += 15
        if avg_ev > 91: score += 10

        st.write(f"🧠 **Cycle Score**: {score}/100")
        if score >= 85:
            st.success("🔥 LOCK")
        elif score >= 70:
            st.info("✅ Lean")
        else:
            st.warning("⚠️ Fade")
    else:
        st.warning("No recent Statcast data for hitter.")
except:
    st.warning("Statcast lookup failed.")
