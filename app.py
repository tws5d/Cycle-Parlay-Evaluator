import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
import requests

def get_wind_text(speed, deg, park_name):
    if speed < 3:
        return "Calm"

    # Approximate batter orientation for Nationals Park (~90° East)
    relative_deg = (deg - 90) % 360

    if 45 <= relative_deg <= 135:
        blowing = "Blowing Left"
    elif 225 <= relative_deg <= 315:
        blowing = "Blowing Right"
    else:
        blowing = "Blowing Center"

    if 60 <= relative_deg <= 120:
        in_out = "Blowing Out to"
    elif 240 <= relative_deg <= 300:
        in_out = "Blowing In to"
    else:
        in_out = "Blowing"

    return f"{in_out} {blowing} ({speed:.1f} mph)"

api_key = "4f676d446a8d39ef55692e6447c5e0f4"

url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
hitters_df = pd.read_csv(url)

unique_players = hitters_df[["player_name", "player_id", "team_id"]].drop_duplicates()
player_name = st.selectbox("Select a hitter:", unique_players["player_name"].unique())

selected_row = unique_players[unique_players["player_name"] == player_name].iloc[0]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]

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
    "Chase Field": "Hitter-Friendly",
    "Globe Life Field": "Hitter-Friendly",
    "Great American Ball Park": "Hitter-Friendly",
    "Fenway Park": "Hitter-Friendly",
    "Coors Field": "Hitter-Friendly",
    "American Family Field": "Neutral",
    "T-Mobile Park": "Neutral",
    "Dodger Stadium": "Neutral",
    "Kauffman Stadium": "Neutral",
    "Oriole Park at Camden Yards": "Neutral",
    "PNC Park": "Neutral",
    "Petco Park": "Pitcher-Friendly",
    "Tropicana Field": "Pitcher-Friendly",
    "Oracle Park": "Pitcher-Friendly",
    "Marlins Park": "Pitcher-Friendly",
    "Rogers Centre": "Pitcher-Friendly",
    "Citizens Bank Park": "Neutral",
    "Yankee Stadium": "Neutral",
    "Wrigley Field": "Neutral",
    "Target Field": "Neutral",
    "Minute Maid Park": "Neutral",
    "Busch Stadium": "Neutral",
    "SunTrust Park": "Neutral",
    "Progressive Field": "Neutral",
    "Truist Park": "Neutral",
    "Nationals Park": "Neutral",
    "Comerica Park": "Neutral",
    "Angel Stadium": "Neutral",
    "Petco Park": "Pitcher-Friendly",
    "Tropicana Field": "Pitcher-Friendly",
}

team_to_park = {
    "Arizona Diamondbacks": "Chase Field",
    "Atlanta Braves": "Globe Life Field",
    "Cincinnati Reds": "Great American Ball Park",
    "Boston Red Sox": "Fenway Park",
    "Colorado Rockies": "Coors Field",
    "Milwaukee Brewers": "American Family Field",
    "Seattle Mariners": "T-Mobile Park",
    "Los Angeles Dodgers": "Dodger Stadium",
    "Kansas City Royals": "Kauffman Stadium",
    "Baltimore Orioles": "Oriole Park at Camden Yards",
    "Pittsburgh Pirates": "PNC Park",
    "San Diego Padres": "Petco Park",
    "Tampa Bay Rays": "Tropicana Field",
    "San Francisco Giants": "Oracle Park",
    "Miami Marlins": "Marlins Park",
    "Toronto Blue Jays": "Rogers Centre",
    "Philadelphia Phillies": "Citizens Bank Park",
    "New York Yankees": "Yankee Stadium",
    "Chicago Cubs": "Wrigley Field",
    "Minnesota Twins": "Target Field",
    "Houston Astros": "Minute Maid Park",
    "St. Louis Cardinals": "Busch Stadium",
    "Atlanta Braves": "SunTrust Park",
    "Cleveland Guardians": "Progressive Field",
    "Atlanta Braves": "Truist Park",
    "Washington Nationals": "Nationals Park",
    "Detroit Tigers": "Comerica Park",
    "Los Angeles Angels": "Angel Stadium"
}

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
        # Nested columns inside col2: pitching stats left, wind right
        stat_col, wind_col = st.columns([3, 1])
        if not df_pitcher.empty:
            avg_ev_allowed = df_pitcher['launch_speed'].mean()
            hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
            total_contact = df_pitcher.shape[0]
            hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
            xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

            xba_tag = "✅" if xba_allowed > 0.280 else "⚠️"
            hard_hit_tag = "✅" if hard_hit_pct_allowed > 35 else "⚠️"
            ev_tag = "✅" if avg_ev_allowed > 89 else "⚠️"

            with stat_col:
                st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed} {xba_tag}")
                st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}% {hard_hit_tag}")
                st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph {ev_tag}")
                st.write(f"🏟️ **Ballpark:** {team_to_park.get(batter_team_name, 'Unknown')} ({ballpark_factors.get(team_to_park.get(batter_team_name, 'Unknown'), 'Unknown')})")

            park_coords = {
                "Chase Field": (33.4458, -112.0669),
                "Globe Life Field": (32.7473, -97.0831),
                "Great American Ball Park": (39.0974, -84.5063),
                "Fenway Park": (42.3467, -71.0972),
                "Coors Field": (39.7556, -104.9942),
                "American Family Field": (43.0281, -87.9712),
                "T-Mobile Park": (47.5914, -122.3325),
                "Dodger Stadium": (34.0739, -118.2400),
                "Kauffman Stadium": (39.0517, -94.4803),
                "Oriole Park at Camden Yards": (39.2839, -76.6219),
                "PNC Park": (40.4473, -80.0053),
                "Petco Park": (32.7076, -117.1570),
                "Tropicana Field": (27.7683, -82.6534),
                "Oracle Park": (37.7786, -122.3893),
                "Marlins Park": (25.7781, -80.2195),
                "Rogers Centre": (43.6414, -79.3894),
                "Citizens Bank Park": (39.9061, -75.1665),
                "Yankee Stadium": (40.8296, -73.9262),
                "Wrigley Field": (41.9484, -87.6553),
                "Target Field": (44.9817, -93.2777),
                "Minute Maid Park": (29.7573, -95.3550),
                "Busch Stadium": (38.6226, -90.1928),
                "SunTrust Park": (33.8908, -84.4677),
                "Progressive Field": (41.4954, -81.6854),
                "Truist Park": (33.8908, -84.4677),
                "Nationals Park": (38.8730, -77.0074),
                "Comerica Park": (42.3390, -83.0485),
                "Angel Stadium": (33.8003, -117.8827)
            }
            coords = park_coords.get(team_to_park.get(batter_team_name, "Unknown"), (40.7128, -74.0060))

            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units=imperial"

            try:
                response = requests.get(weather_url)
                weather_data = response.json()
                if 'wind' in weather_data and 'speed' in weather_data['wind'] and 'deg' in weather_data['wind']:
                    wind_speed = weather_data['wind']['speed']
                    wind_deg = weather_data['wind']['deg']
                    wind_text = get_wind_text(wind_speed, wind_deg, team_to_park.get(batter_team_name, "Unknown"))
                    with wind_col:
                        wind_html = f"""
                        <div style='
                            font-size:24px; 
                            display: flex; 
                            flex-direction: column; 
                            justify-content: center; 
                            height: 100%;
                            text-align: center;
                            color: white;
                        '>
                            <strong>Wind</strong>
                            <span>{wind_text}</span>
                        </div>
                        """
                        st.markdown(wind_html, unsafe_allow_html=True)
                else:
                    with wind_col:
                        st.warning("⚠️ Wind data not available for this location.")
            except Exception as e:
                with wind_col:
                    st.warning(f"⚠️ Could not fetch wind data: {e}")

            score = 50
            if xba_allowed > 0.280: score += 10
            if hard_hit_pct_allowed > 40: score += 10
            if avg_ev_allowed > 89: score += 5
        else:
            st.warning("No recent data for pitcher.")
else:
    st.warning("❗ No probable pitcher found for this matchup.")

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

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ABs", total_abs)
    col2.metric("Hits", f"{total_hits}", f"Max: {max_hits}")
    col3.metric("Total Bases", f"{total_bases}", f"Max: {max_bases}")
    col4.metric("RBIs", f"{total_rbis}", f"Max: {max_rbis}")
    col5.metric("HRs", total_hrs)

    col1, col2, col3 = st.columns(3)
    col1.metric("AVG", f"{avg}")
    col2.metric("OBP", f"{obp}")
    col3.metric("SLG", f"{slg}")

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
