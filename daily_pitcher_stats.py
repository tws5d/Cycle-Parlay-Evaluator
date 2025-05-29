import requests
import pandas as pd
from datetime import date, timedelta

# Get today's date
today = date.today().isoformat()

# Step 1: Get today's games from MLB Stats API
def get_active_pitchers(team_ids):
    pitchers = []
    for team_id in team_ids:
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/active"
        r = requests.get(url).json()
        for player in r.get("roster", []):
            person = player.get("person", {})
            position = player.get("position", {}).get("abbreviation")
            if position == "P":  # Only pitchers
                pitchers.append({
                    "id": person.get("id", "N/A"),
                    "name": person.get("fullName", "TBD"),
                    "team": player.get("team", {}).get("name", "")
                })

    # ✅ Debug output (inside the function, right before return)
    print(f"Found {len(pitchers)} pitchers")
    for p in pitchers:
        print(f"{p['name']} ({p['id']}) - {p['team']}")
    
    return pitchers

print(f"Found {len(pitchers)} pitchers")
for p in pitchers:
    print(f"{p['name']} ({p['id']}) - {p['team']}")


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
    # Example: a few team IDs — you can expand this list
    team_ids = [121, 147, 139, 110]  # NYY, NYM, SEA, BAL — adjust as needed

    pitchers = get_active_pitchers(team_ids)
    all_rows = []

    for pitcher in pitchers:
        if pitcher["id"] == "N/A":
            continue
        print(f"Fetching logs for {pitcher['name']} ({pitcher['id']})")
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

