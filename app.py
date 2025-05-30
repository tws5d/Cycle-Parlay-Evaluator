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

# Load pitcher data
pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

# Try to find opposing pitcher using team_id match (simple method for now)
pitcher_row = pitchers_df[pitchers_df["Team"].str.contains(str(team_id), na=False)]
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
        end_date = datetime._
