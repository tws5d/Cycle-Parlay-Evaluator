import requests
import pandas as pd
from datetime import date, timedelta

# Get today's date
today = date.today().isoformat()

# Step 1: Get today's games from MLB Stats API
def get_today_pitchers():
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": today}
    r = requests.get(url, params=params)
    games = r.json().get("dates", [])[0].get("games", [])
    
    pitchers = []
    for game in games:
        for side in ["home", "away"]:
            team = game["teams"][side]
            pitcher = team.get("probablePitcher") or team.get("pitcher")
    
            # Add fallback for missing or partial data
            name = pitcher["fullName"] if isinstance(pitcher, dict) and "fullName" in pitcher else "TBD"
            pitcher_id = pitcher["id"] if isinstance(pitcher, dict) and "id" in pitcher else "N/A"

            pitchers.append({
                "name": name,
                "id": pitcher_id,
                "team": team["team"]["name"]
            })
  
    return pitchers

# Step 2: Get recent statcast performance for each pitcher
def get_pitcher_game_logs(pitcher_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "pitching",
        "gameType": "R",
        "limit": 5  # Last 5 starts
    }
    r = requests.get(url, params=params).json()
    return r.get("stats", [{}])[0].get("splits", [])

# Step 3: Build the CSV
def build_pitcher_file():
    pitchers = get_today_pitchers()
    all_rows = []

    for pitcher in pitchers:
        logs = get_pitcher_game_logs(pitcher["id"])
        for game in logs:
            stat = game["stat"]
            all_rows.append({
                "pitcher_id": pitcher["id"],
                "pitcher_name": pitcher["name"],
                "team": pitcher["team"],
                "date": game.get("date", ""),
                "innings_pitched": stat.get("inningsPitched", "0.0"),
                "earned_runs": stat.get("earnedRuns", 0),
                "strike_outs": stat.get("strikeOuts", 0),
                "base_on_balls": stat.get("baseOnBalls", 0),
                "hits": stat.get("hits", 0),
                "pitches_thrown": stat.get("numberOfPitches", 0),
                "whip": stat.get("whip", 0),
                "era": stat.get("era", 0)
            })

    df = pd.DataFrame(all_rows)
    df.to_csv("latest_pitchers.csv", index=False)
    print(f"Saved {len(df)} pitcher logs to latest_pitchers.csv")

# Run it
if __name__ == "__main__":
    build_pitcher_file()

