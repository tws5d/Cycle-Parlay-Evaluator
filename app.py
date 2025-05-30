import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
import requests
import matplotlib.pyplot as plt
import numpy as np

def generate_wind_compass(speed, direction_deg):
    fig, ax = plt.subplots(figsize=(2.5, 2.5), subplot_kw={'projection': 'polar'})
    theta = np.radians(direction_deg)
    ax.arrow(theta, 0, 0, 1, width=0.05, head_width=0.2, head_length=0.3, fc='blue', ec='blue')
    ax.set_rticks([])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{speed} mph", va='bottom', fontsize=10)
    plt.tight_layout()
    fig.subplots_adjust(top=0.85)
    fig.suptitle("Wind Direction", fontsize=12)
    return fig

# --- Your API key for OpenWeather ---
api_key = "4f676d446a8d39ef55692e6447c5e0f4"

# Load daily hitter file
url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
hitters_df = pd.read_csv(url)

# Unique hitter list
unique_players = hitters_df[["player_name", "player_id", "team_id"]].drop_duplicates()
player_name = st.selectbox("Select a hitter:", unique_players["player_name"].unique())

# Get batter info
selected_row = unique_players[unique_players["player_name"] == player_name].iloc[0]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]

# Team & ballpark maps
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

ballpark_factors = {
    "Coors Field": "Hitter-Friendly",
    "Great American Ball Park": "Hitter-Friendly",
    "Fenway Park": "Hitter-Friendly",
    "Dodger Stadium": "Neutral",
    "Wrigley Field": "Neutral",
    "Yankee Stadium": "Neutral",
    "Petco Park": "Pitcher-Friendly",
    "Tropicana Field": "Pitcher-Friendly",
    "Oracle Park": "Pitcher-Friendly",
    "Nationals Park": "Neutral"
}

team_to_park = {
    "Washington Nationals": "Nationals Park",
    "Colorado Rockies": "Coors Field",
    "Cincinnati Reds": "Great American Ball Park",
    "Boston Red Sox": "Fenway Park",
    "San Diego Padres": "Petco Park",
    "Tampa Bay Rays": "Tropicana Field",
    "San Francisco Giants": "Oracle Park"
}

home_park = team_to_park.get(batter_team_name, "Unknown")
park_rating = ballpark_factors.get(home_park, "Unknown")

# Load pitcher data
pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

pitcher_row = pitchers_df[pitchers_df["Opponent"] == batter_team_name]
pitcher_name = None
pitcher_id = None

if not pitcher_row.empty:
    pitcher_name = pitcher_row.iloc[0]["Pitcher Name"]
    pitcher_id = int(pitcher_row.iloc[0]["MLB ID"])
    st.write(f"🧱 Probable Pitcher: {pitcher_name}")

    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)

    image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{batter_id}/headshot/67/current.png"

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(image_url, width=100)
    with col2:
        if not df_pitcher.empty:
            avg_ev_allowed = df_pitcher['launch_speed'].mean()
            hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
            total_contact = df_pitcher.shape[0]
            hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
            xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

            xba_tag = "✅" if xba_allowed > 0.280 else "⚠️"
            hard_hit_tag = "✅" if hard_hit_pct_allowed > 35 else "⚠️"
            ev_tag = "✅" if avg_ev_allowed > 89 else "⚠️"

            st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed} {xba_tag}")
            st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}% {hard_hit_tag}")
            st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph {ev_tag}")
            st.write(f"🏟️ **Ballpark:** {home_park} ({park_rating})")

            # Fetch wind data from OpenWeather
            city = home_park.split()[0]  # crude, but often works (e.g. "Nationals")
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
            try:
                response = requests.get(weather_url)
                weather_data = response.json()
                wind_speed = weather_data['wind']['speed']
                wind_deg = weather_data['wind']['deg']

                # Generate and display wind compass
                fig = generate_wind_compass(wind_speed, wind_deg)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"⚠️ Could not fetch wind data: {e}")

            score = 50
            if xba_allowed > 0.280: score += 10
            if hard_hit_pct_allowed > 40: score += 10
            if avg_ev_allowed > 89: score += 5
        else:
            st.warning("No recent data for pitcher.")
else:
    st.warning("❗ No probable pitcher found for this matchup.")

# Batter Statcast data
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

    # Load hitter daily stats
    daily_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
    full_df = pd.read_csv(daily_url)
    recent_df = full_df[(full_df["player_id"] == batter_id) & (full_df["game_date"] >= start_date)]

    total_abs = recent_df["at_bats"].sum()
    total_hits = recent_df["hits"].sum()
    total_rbis = recent_df["rbi"].sum()
    total_hrs = recent_df["home_runs"].sum()
    total_bases = (recent_df["hits"] + 2 * recent_df["home_runs"]).sum()
    max_hits = recent_df["hits"].max()
    max_rbis = recent_df["rbi"].max()
    max_bases = (recent_df["hits"] + 2 * recent_df["home_runs"]).max()
    avg = round(recent_df["avg"].mean(), 3)
    obp = round(recent_df["obp"].mean(), 3)
    slg = round(recent_df["slg"].mean(), 3)

    # Stat Summary - Totals
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ABs", total_abs)
    col2.metric("Hits", f"{total_hits}", f"Max: {max_hits}")
    col3.metric("Total Bases", f"{total_bases}", f"Max: {max_bases}")
    col4.metric("RBIs", f"{total_rbis}", f"Max: {max_rbis}")
    col5.metric("HRs", total_hrs)

    # Averages
    col1, col2, col3 = st.columns(3)
    col1.metric("AVG", f"{avg}")
    col2.metric("OBP", f"{obp}")
    col3.metric("SLG", f"{slg}")

    # Add indicators
    exit_tag = "✅" if avg_exit_velo > 91 else "⚠️"
    hard_hit_tag = "✅" if hard_hit_pct > 45 else "⚠️"
    xba_tag = "✅" if xba > 0.300 else "⚠️"

    st.write(f"**Average Exit Velocity:** {round(avg_exit_velo, 1)} mph {exit_tag}")
    st.write(f"**Hard Hit %:** {hard_hit_pct}% {hard_hit_tag}")
    st.write(f"**xBA (Expected BA):** {xba} {xba_tag}")

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
