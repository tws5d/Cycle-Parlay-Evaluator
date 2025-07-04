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
            person_id = player["person"]["id"]
            handedness = ""
            try:
                details = requests.get(f"https://statsapi.mlb.com/api/v1/people/{person_id}").json()
                handedness = details["people"][0]["batSide"]["code"]
            except Exception as e:
                print(f"⚠️ Could not fetch handedness for {person_id}: {e}")

            hitters.append({
                "player_id": person_id,
                "full_name": player["person"]["fullName"],
                "team_id": team_id,
                "bat_side": handedness
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
                doubles = stats.get("doubles", 0)
                triples = stats.get("triples", 0)
                home_runs = stats.get("homeRuns", 0)
                hits = stats.get("hits", 0)
                
                row = {
                    "player_id": hitter["player_id"],
                    "player_name": hitter["full_name"],
                    "team_id": hitter["team_id"],
                    "team_name": team_info.get(hitter["team_id"], "Unknown"),
                    "game_date": log.get("date", ""),
                    "at_bats": stats.get("atBats", 0),
                    "hits": stats.get("hits", 0),
                    "doubles": doubles,
                    "triples": triples,
                    "home_runs": stats.get("homeRuns", 0),
                    "rbi": stats.get("rbi", 0),
                    "strike_outs": stats.get("strikeOuts", 0),
                    "base_on_balls": stats.get("baseOnBalls", 0),
                    "hit_by_pitch": stats.get("hitByPitch", 0),
                    "sac_flies": stats.get("sacFlies", 0),
                    "bat_side": hitter.get("bat_side", ""),
                    "avg": stats.get("avg", 0),
                    "obp": stats.get("obp", 0),
                    "slg": stats.get("slg", 0),
                    "ops": stats.get("ops", 0),
                    "runs": stats.get("runs", 0),
                    "stolen_bases": stats.get("stolenBases", 0),
                    "total_bases": stats.get("totalBases", 0),
                }
                all_data.append(row)

    df = pd.DataFrame(all_data)
    df.to_csv("latest_hitters.csv", index=False)
    print(f"Saved data for {len(df)} hitter game logs.")

# Run the script
if __name__ == "__main__":
    build_daily_hitter_csv()

import subprocess
import datetime

def git_push_csv(file_path):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Update latest_hitters.csv ({timestamp})"

    try:
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ latest_pitchers.csv pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print("❌ Git push failed:", e)

# Call it at the end of your script
git_push_csv("latest_hitters.csv")
