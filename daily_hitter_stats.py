import requests
import pandas as pd
from datetime import date

# Step 1: Get today's team IDs
def get_today_team_ids():
    today = date.today().isoformat()
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": today}
    r = requests.get(url, params=params)
    data = r.json()

    team_ids = []
    for game in data.get("dates", [])[0].get("games", []):
        team_ids.append(game["teams"]["away"]["team"]["id"])
        team_ids.append(game["teams"]["home"]["team"]["id"])

    return list(set(team_ids))

# Step 2: Get all hitters from a team
def get_team_hitters(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    r = requests.get(url)
    roster = r.json().get("roster", [])
    hitters = []
    for player in roster:
        pos = player["position"]["abbreviation"]
        if pos in ["1B", "2B", "3B", "SS", "LF", "CF", "RF", "C", "DH"]:
            hitters.append({
                "player_id": player["person"]["id"],
                "full_name": player["person"]["fullName"],
                "team_id": team_id
            })
    return hitters

# Step 3: Get last 10 game logs for a hitter
def get_last_10_hitter_games(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "hitting",
        "gameType": "R",
        "limit": 10
    }
    r = requests.get(url, params=params)
    try:
        splits = r.json()["stats"][0]["splits"]
        return splits
    except:
        return []

# Step 4: Run it all and save to CSV
def build_daily_hitter_csv():
    team_info = {team['id']: team['clubName'] for team in requests.get('https://statsapi.mlb.com/api/v1/teams?sportId=1').json()['teams']}
    all_data = []

    teams = get_today_team_ids()
    print(f"Found {len(teams)} teams playing today.")

    for team_id in teams:
        hitters = get_team_hitters(team_id)
        for hitter in hitters:
            logs = get_last_10_hitter_games(hitter["player_id"])
            for log in logs:
                stats = log.get("stat", {})
                row = {
                    "player_id": hitter["player_id"],
                    "player_name": hitter["full_name"],
                    "team_id": hitter["team_id"],
                    "team_name": team_info.get(hitter["team_id"], "Unknown"),
                    "game_date": log.get("date", ""),
                    "at_bats": stats.get("atBats", 0),
                    "hits": stats.get("hits", 0),
                    "home_runs": stats.get("homeRuns", 0),
                    "rbi": stats.get("rbi", 0),
                    "strike_outs": stats.get("strikeOuts", 0),
                    "base_on_balls": stats.get("baseOnBalls", 0),
                    "avg": stats.get("avg", 0),
                    "obp": stats.get("obp", 0),
                    "slg": stats.get("slg", 0),
                    "ops": stats.get("ops", 0),
                }
                all_data.append(row)

    df = pd.DataFrame(all_data)
    df.to_csv("latest_hitters.csv", index=False)
    print(f"Saved data for {len(df)} hitter game logs.")

# Run the script
if __name__ == "__main__":
    build_daily_hitter_csv()
