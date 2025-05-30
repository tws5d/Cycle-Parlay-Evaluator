import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta

# Load your daily hitter file (from GitHub)
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
    137: "Los Angeles Dodgers",  # Assuming 137 is Dodgers
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
    120: "Texas Rangers",
    136: "Toronto Blue Jays",    # Changed from 137 to avoid overwrite
    120: "Washington Nationals"  # Changed from 120: Texas to 136
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

            st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed}")
            st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}%")
            st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph")

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
