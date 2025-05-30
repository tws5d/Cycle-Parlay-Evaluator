import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
import requests

def get_wind_text(speed, deg):
    if speed < 3:
        return "Calm", "⚪️"
    relative_deg = (deg - 90) % 360
    if 45 <= relative_deg <= 135:
        blowing = "Blowing Left"
    elif 225 <= relative_deg <= 315:
        blowing = "Blowing Right"
    else:
        blowing = "Blowing Center"
    if 60 <= relative_deg <= 120:
        in_out = "Blowing Out to"
        emoji = "✅" if speed >= 10 else "🟡" if speed >= 5 else "⚪️"
    elif 240 <= relative_deg <= 300:
        in_out = "Blowing In to"
        emoji = "⚠️" if speed >= 10 else "🟠" if speed >= 5 else "⚪️"
    else:
        in_out = "Blowing"
        emoji = "⚪️"
    return f"{in_out} {blowing} ({speed:.1f} mph)", emoji

api_key = "4f676d446a8d39ef55692e6447c5e0f4"

url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
hitters_df = pd.read_csv(url)

unique_players = hitters_df[["player_name", "player_id", "team_id"]].drop_duplicates()
player_name = st.selectbox("Select a hitter:", unique_players["player_name"].unique())

selected_row = unique_players[unique_players["player_name"] == player_name].iloc[0]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]

# mappings
team_id_map = {...}  # [same as yours]
ballpark_factors = {...}  # [same as yours]
team_to_park = {...}  # [same as yours]
park_coords = {...}  # [same as yours]

batter_team_name = team_id_map.get(team_id)
pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

pitcher_row = pitchers_df[pitchers_df["Opponent"] == batter_team_name]
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
        stat_col, _ = st.columns([3, 1])
        if not df_pitcher.empty:
            avg_ev_allowed = df_pitcher['launch_speed'].mean()
            hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
            total_contact = df_pitcher.shape[0]
            hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
            xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

            xba_tag = "✅" if xba_allowed > 0.280 else "⚠️"
            hard_hit_tag = "✅" if hard_hit_pct_allowed > 35 else "⚠️"
            ev_tag = "✅" if avg_ev_allowed > 89 else "⚠️"

            park_name = team_to_park.get(batter_team_name, "Unknown")
            park_type = ballpark_factors.get(park_name, "Unknown")
            park_emoji = "⚾" if park_type == "Hitter-Friendly" else "🛡️" if park_type == "Pitcher-Friendly" else "⚖️"

            with stat_col:
                st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed} {xba_tag}")
                st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}% {hard_hit_tag}")
                st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph {ev_tag}")
                st.write(f"🏟️ **Ballpark:** {park_emoji} {park_name} ({park_type})")

                coords = park_coords.get(park_name, (40.7128, -74.0060))
                try:
                    weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units=imperial"
                    response = requests.get(weather_url)
                    weather_data = response.json()
                    if "wind" in weather_data and "speed" in weather_data["wind"] and "deg" in weather_data["wind"]:
                        wind_speed = weather_data["wind"]["speed"]
                        wind_deg = weather_data["wind"]["deg"]
                        wind_text, wind_emoji = get_wind_text(wind_speed, wind_deg)
                        st.markdown(f"**Wind**  \n{wind_text}  \n{wind_emoji}")
                except:
                    st.markdown("**Wind**  \nError retrieving wind data.")

            score = 50
            if xba_allowed > 0.280: score += 10
            if hard_hit_pct_allowed > 40: score += 10
            if avg_ev_allowed > 89: score += 5
else:
    st.warning("❗ No probable pitcher found for this matchup.")

# --- Hitter statcast ---
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

    full_df = pd.read_csv(url)
    recent_df = full_df[(full_df["player_id"] == batter_id) & (full_df["game_date"] >= start_date)]

    total_abs = recent_df["at_bats"].sum()
    total_hits = recent_df["hits"].sum()
    total_rbis = recent_df["rbi"].sum()
    total_hrs = recent_df["home_runs"].sum()
    total_bases = (recent_df["hits"] + 2 * recent_df["home_runs"]).sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ABs", total_abs)
    col2.metric("Hits", total_hits)
    col3.metric("Total Bases", total_bases)
    col4.metric("RBIs", total_rbis)
    col5.metric("HRs", total_hrs)

    avg = round(recent_df["avg"].mean(), 3)
    obp = round(recent_df["obp"].mean(), 3)
    slg = round(recent_df["slg"].mean(), 3)

    col1, col2, col3 = st.columns(3)
    col1.metric("AVG", avg)
    col2.metric("OBP", obp)
    col3.metric("SLG", slg)

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

    if score >= 85:
        st.success("🔥 Strong Pick")
    elif score >= 70:
        st.info("✅ Solid Pick")
    else:
        st.warning("⚠️ Risky Pick")
else:
    st.warning("No Statcast data found for this timeframe.")
