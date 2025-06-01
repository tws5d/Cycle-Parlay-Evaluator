import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
import requests

def get_wind_text(speed, deg, park_name):
    if speed < 3:
        return "Calm"
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

def get_wind_image(speed, deg):
    if speed is None or speed == 0:
        return "No.Wind.Data.Available.png"
    relative_deg = (deg - 90) % 360
    if 45 <= relative_deg <= 135:
        return "Blowing.Left.png"
    elif (135 < relative_deg <= 180) or (0 <= relative_deg < 45):
        return "Blowing.Out.Center.Left.png"
    elif (180 <= relative_deg <= 225) or (315 <= relative_deg < 360):
        return "Blowing.Out.Center.png"
    elif 225 < relative_deg < 270:
        return "Blowing.Out.Center.Right.png"
    elif 270 <= relative_deg <= 315:
        return "Blowing.Right.png"
    else:
        return "Blowing.In.png"

api_key = "4f676d446a8d39ef55692e6447c5e0f4"

url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_hitters.csv"
@st.cache_data(ttl=60)
def load_hitters():
    return pd.read_csv(url)

hitters_df = load_hitters()

unique_players = hitters_df[["player_name", "player_id", "team_id", "team_name", "bat_side"]].drop_duplicates()

# Add last name for sorting
unique_players["last_name"] = unique_players["player_name"].apply(lambda x: x.split()[-1])

# Sort by team then last name
unique_players = unique_players.sort_values(by=["team_name", "last_name"])

# Display format: TEAM - First Last
unique_players["display_name"] = unique_players.apply(
    lambda row: f"{row['team_name']} - {row['player_name']} ({row['bat_side']})", axis=1
)

# Dropdown with formatted names, but return real player_name
selected_display = st.selectbox("Select a hitter:", unique_players["display_name"])
selected_row = unique_players[unique_players["display_name"] == selected_display].iloc[0]

player_name = selected_row["player_name"]
batter_id = selected_row["player_id"]
team_id = selected_row["team_id"]
batter_team_name = selected_row["team_name"]

name_corrections = {
    "Arizona Diamondbacks": "Diamondbacks",
    "Baltimore Orioles": "Orioles",
    "Atlanta Braves": "Braves",
    "Boston Red Sox": "Red Sox",
    "Chicago Cubs": "Cubs",
    "Chicago White Sox": "White Sox",
    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",
    "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",
    "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",
    "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",
    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",
    "Minnesota Twins": "Twins",
    "New York Mets": "Mets",
    "New York Yankees": "Yankees",
    "Oakland Athletics": "Athletics",
    "Philadelphia Phillies": "Phillies",
    "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",
    "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",
    "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",
    "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",
    "Washington Nationals": "Nationals"
}

short_team_name = name_corrections.get(batter_team_name, batter_team_name)

# Latitude and Longitude for each MLB ballpark
park_coords = {
    "Angel Stadium": (33.8003, -117.8827),
    "Busch Stadium": (38.6226, -90.1928),
    "Chase Field": (33.4455, -112.0667),
    "Citizens Bank Park": (39.9057, -75.1665),
    "Citi Field": (40.7571, -73.8458),
    "Comerica Park": (42.3390, -83.0485),
    "Coors Field": (39.7559, -104.9942),
    "Dodger Stadium": (34.0739, -118.2400),
    "Fenway Park": (42.3467, -71.0972),
    "Globe Life Field": (32.7473, -97.0847),
    "Great American Ball Park": (39.0972, -84.5078),
    "Guaranteed Rate Field": (41.8309, -87.6345),
    "Kauffman Stadium": (39.0517, -94.4803),
    "Marlins Park": (25.7781, -80.2195),  # Marlins Park
    "Minute Maid Park": (29.7573, -95.3555),
    "Nationals Park": (38.8728, -77.0074),
    "Oakland Coliseum": (37.7516, -122.2005),
    "Oracle Park": (37.7786, -122.3893),
    "Oriole Park at Camden Yards": (39.2839, -76.6217),
    "Petco Park": (32.7073, -117.1573),
    "PNC Park": (40.4469, -80.0057),
    "Progressive Field": (41.4962, -81.6852),
    "Rogers Centre": (43.6414, -79.3894),
    "T-Mobile Park": (47.5914, -122.3325),
    "Target Field": (44.9817, -93.2783),
    "Tropicana Field": (27.7683, -82.6534),
    "Truist Park": (33.8909, -84.4677),
    "Wrigley Field": (41.9484, -87.6553),
    "Yankee Stadium": (40.8296, -73.9262),
    "American Family Field": (43.0280, -87.9712)
}

ballpark_factors = {
    "Chase Field": "Hitter-Friendly", "Globe Life Field": "Hitter-Friendly", "Great American Ball Park": "Hitter-Friendly",
    "Fenway Park": "Hitter-Friendly", "Coors Field": "Hitter-Friendly", "American Family Field": "Neutral",
    "T-Mobile Park": "Neutral", "Dodger Stadium": "Neutral", "Kauffman Stadium": "Neutral",
    "Oriole Park at Camden Yards": "Neutral", "PNC Park": "Neutral", "Petco Park": "Pitcher-Friendly",
    "Tropicana Field": "Pitcher-Friendly", "Oracle Park": "Pitcher-Friendly", "Marlins Park": "Pitcher-Friendly",
    "Rogers Centre": "Pitcher-Friendly", "Citizens Bank Park": "Neutral", "Yankee Stadium": "Neutral",
    "Wrigley Field": "Neutral", "Target Field": "Neutral", "Minute Maid Park": "Neutral",
    "Busch Stadium": "Neutral", "SunTrust Park": "Neutral", "Progressive Field": "Neutral",
    "Truist Park": "Neutral", "Nationals Park": "Neutral", "Comerica Park": "Neutral",
    "Angel Stadium": "Neutral"
}

team_to_park = {
    "Diamondbacks": "Chase Field",
    "Braves": "Truist Park",
    "Reds": "Great American Ball Park",
    "Red Sox": "Fenway Park",
    "Rockies": "Coors Field",
    "Brewers": "American Family Field",
    "Mariners": "T-Mobile Park",
    "Dodgers": "Dodger Stadium",
    "Royals": "Kauffman Stadium",
    "Orioles": "Oriole Park at Camden Yards",
    "Pirates": "PNC Park",
    "Padres": "Petco Park",
    "Rays": "Tropicana Field",
    "Giants": "Oracle Park",
    "Marlins": "Marlins Park",
    "Blue Jays": "Rogers Centre",
    "Phillies": "Citizens Bank Park",
    "Yankees": "Yankee Stadium",
    "Cubs": "Wrigley Field",
    "Twins": "Target Field",
    "Astros": "Minute Maid Park",
    "Cardinals": "Busch Stadium",
    "Guardians": "Progressive Field",
    "Nationals": "Nationals Park",
    "Tigers": "Comerica Park",
    "Angels": "Angel Stadium",
    "Mets": "Citi Field",
    "White Sox": "Guaranteed Rate Field",
    "Athletics": "Oakland Coliseum",
    "Rangers": "Globe Life Field"
}

pitchers_url = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/latest_pitchers.csv"
pitchers_df = pd.read_csv(pitchers_url)

short_team_name = name_corrections.get(batter_team_name, batter_team_name)

pitcher_row = pitchers_df[pitchers_df["Opponent"].str.contains(short_team_name, case=False, na=False)]

if pitcher_row.empty:
    pitcher_row = pitchers_df[pitchers_df["Team"].str.contains(batter_team_name, case=False, na=False)]
pitcher_name = None
pitcher_id = None

if not pitcher_row.empty:
    pitcher_name = pitcher_row.iloc[0]["Pitcher Name"]
    pitcher_id = int(pitcher_row.iloc[0]["MLB ID"])
    era = pitcher_row.iloc[0].get("ERA", "")
    baa = pitcher_row.iloc[0].get("BAA", "")
    opsa = pitcher_row.iloc[0].get("OPSa", "")

    st.write(f"🧤 Opposing Pitcher: {pitcher_name} ({pitcher_row.iloc[0]['Throws']}) | ERA: {era} | BAA: {baa} | OPSa: {opsa}")
    
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)

    image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{batter_id}/headshot/67/current.png"

    col1, col2 = st.columns([1, 5.5])
    with col1:
        st.image(image_url, width=100)
    with col2:
        stat_col, weather_col, wind_col = st.columns([3, 1, 1])
        
        if not df_pitcher.empty:
            avg_ev_allowed = df_pitcher['launch_speed'].mean()
            hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
            total_contact = df_pitcher.shape[0]
            hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
            xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

            xba_tag = "✅" if xba_allowed > 0.280 else "⚠️"
            hard_hit_tag = "✅" if hard_hit_pct_allowed > 35 else "⚠️"
            ev_tag = "✅" if avg_ev_allowed > 89 else "⚠️"

            # Find matchup row for batter's team in pitchers_df
            matchup_row = pitchers_df[(pitchers_df["Opponent"] == batter_team_name) | (pitchers_df["Team"] == batter_team_name)]

            if not matchup_row.empty:
                home_team = matchup_row.iloc[0]["Team"]  # Assuming "Team" is home team
            else:
                home_team = batter_team_name

            name_corrections = {
                "Arizona Diamondbacks": "Diamondbacks",
                "Baltimore Orioles": "Orioles",
                "Atlanta Braves": "Braves",
                "Boston Red Sox": "Red Sox",
                "Chicago Cubs": "Cubs",
                "Chicago White Sox": "White Sox",
                "Cincinnati Reds": "Reds",
                "Cleveland Guardians": "Guardians",
                "Colorado Rockies": "Rockies",
                "Detroit Tigers": "Tigers",
                "Houston Astros": "Astros",
                "Kansas City Royals": "Royals",
                "Los Angeles Angels": "Angels",
                "Los Angeles Dodgers": "Dodgers",
                "Miami Marlins": "Marlins",
                "Milwaukee Brewers": "Brewers",
                "Minnesota Twins": "Twins",
                "New York Mets": "Mets",
                "New York Yankees": "Yankees",
                "Oakland Athletics": "Athletics",
                "Philadelphia Phillies": "Phillies",
                "Pittsburgh Pirates": "Pirates",
                "San Diego Padres": "Padres",
                "San Francisco Giants": "Giants",
                "Seattle Mariners": "Mariners",
                "St. Louis Cardinals": "Cardinals",
                "Tampa Bay Rays": "Rays",
                "Texas Rangers": "Rangers",
                "Toronto Blue Jays": "Blue Jays",
                "Washington Nationals": "Nationals"
            }
            
            # Get ballpark info for the home team
            lookup_name = name_corrections.get(home_team, home_team)
            park_name = team_to_park.get(lookup_name, "Unknown")
            # Get coordinates for the current ballpark
            coords = park_coords.get(park_name)
            wind_speed = None
            wind_deg = None           
            
            if coords:
                lat, lon = coords
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
                wind_description = None
                try:
                    response = requests.get(weather_url)
                    data = response.json()
                    wind_speed = data["wind"]["speed"]
                    wind_deg = data["wind"]["deg"]
                    wind_description = get_wind_text(wind_speed, wind_deg, park_name)
                    wind_image_file = get_wind_image(wind_speed, wind_deg)
                except Exception as e:
                    st.warning("Failed to fetch wind data.")
                    st.text(e)
                    wind_speed = None
                    wind_deg = None
                    wind_image_file = "No.Wind.Data.Available.png"

                
            else:
                st.warning(f"No coordinates found for {park_name}")

            park_type = ballpark_factors.get(park_name, "Unknown")
            park_emoji = "⚾" if park_type == "Hitter-Friendly" else "🛡️" if park_type == "Pitcher-Friendly" else "⚖️"
            
            with wind_col:
                st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
                
                if wind_speed and wind_speed > 0:
                    wind_image_path = f"https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/{wind_image_file}"
                    st.markdown(f"<img src='{wind_image_path}' width='140' style='margin-top: -20px;'>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; margin-left: -1px; margin-top: -10px;'>{wind_speed:.1f} mph</div>", unsafe_allow_html=True)
                    
                else:
                    wind_image_path = "https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/No.Wind.Data.Available.png"
                    st.image(wind_image_path, width=100)

                st.markdown("</div>", unsafe_allow_html=True)

            with stat_col:
                st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed} {xba_tag}")
                st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}% {hard_hit_tag}")
                st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph {ev_tag}")
                st.write(f"🏟️ **Ballpark:** {park_emoji} {park_name} ({park_type})")

            score = 50
            if xba_allowed > 0.280: score += 10
            if hard_hit_pct_allowed > 40: score += 10
            if avg_ev_allowed > 89: score += 5

            with weather_col:
                if data:
                    condition = data["weather"][0]["main"] if "weather" in data else "Unknown"
                    temperature = round(data["main"]["temp"]) if "main" in data else None
                    icon_map = {
                        "Clear": "Sunny.png",
                        "Clouds": "Cloudy.png",
                        "Rain": "Rainy.png"
                        }
                    icon_file = icon_map.get(condition, "No.Weather.Data.Available.png")
                    icon_url = f"https://raw.githubusercontent.com/tws5d/Cycle-Parlay-Evaluator/main/{icon_file}"

                    st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
                    st.markdown(f"<img src='{icon_url}' width='90' style='margin-top: -10px; margin-bottom: 4px;'>", unsafe_allow_html=True)
                    if temperature is not None:
                        st.markdown(f"<div style='margin-left: 30px; margin-top: -8px;'>{temperature}°F</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            st.warning("No recent data for pitcher.")
else:
    st.warning("❗ No opposing pitcher found for this matchup.")

end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
st.write(f"📅 Two-Week Rolling Stats ({start_date} - {end_date})")

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
    avg = round(recent_df.sort_values("game_date", ascending=False).iloc[0]["avg"], 3)
    obp = round(recent_df.sort_values("game_date", ascending=False).iloc[0]["obp"], 3)
    slg = round(recent_df.sort_values("game_date", ascending=False).iloc[0]["slg"], 3)
    

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    col1.metric("ABs", total_abs)
    with col2:
        st.metric("Hits", total_hits)
        st.markdown(f"<div style='color: green; font-size: 12px; margin-top: -10px; margin-left: 6px;'>Max: {max_hits}</div>", unsafe_allow_html=True)

    walks = recent_df["base_on_balls"].sum()
    col3.metric("Walks", walks)
    runs = recent_df["runs"].sum()
    max_runs = recent_df["runs"].max()
    
    with col4:
        st.metric("Runs", runs)
        st.markdown(f"<div style='color: green; font-size: 12px; margin-top: -10px; margin-left: 6px;'>Max: {max_runs}</div>", unsafe_allow_html=True)
    
    
    with col5:
        st.metric("RBIs", total_rbis)
        st.markdown(f"<div style='color: green; font-size: 12px; margin-top: -10px; margin-left: 6px;'>Max: {max_rbis}</div>", unsafe_allow_html=True)
    
    stolen_bases = recent_df["stolen_bases"].sum()
    col6.metric("SBs", stolen_bases)
    col7.metric("HRs", total_hrs)
    
    with col8:
        st.metric("TBs", total_bases)
        st.markdown(f"<div style='color: green; font-size: 12px; margin-top: -10px; margin-left: 6px;'>Max: {max_bases}</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Season AVG", f"{avg:.3f}")
    col2.metric("Season OBP", f"{obp:.3f}")
    col3.metric("Season SLG", f"{slg:.3f}")

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
