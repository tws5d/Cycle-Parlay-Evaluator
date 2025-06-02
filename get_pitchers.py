import requests
import pandas as pd
from datetime import datetime

today = datetime.today().strftime('%Y-%m-%d')
def get_throwing_hand(pitcher_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}"
        response = requests.get(url)
        data = response.json()
        return data["people"][0]["pitchHand"]["code"]  # "R", "L", or "S"
    except:
        return "?"

# MLB Schedule endpoint for only today
url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"

response = requests.get(url)
data = response.json()

rows = []

for date in data["dates"]:
    for game in date["games"]:
        for side in ['home', 'away']:
            team = game["teams"][side]["team"]["name"]
            opp = game["teams"]["away"]["team"]["name"] if side == "home" else game["teams"]["home"]["team"]["name"]
            pitcher = game["teams"][side].get("probablePitcher")
            if pitcher:
                # Pull last 5 game logs
                gamelog_url = f"https://statsapi.mlb.com/api/v1/people/{pitcher['id']}/stats?stats=gameLog&group=pitching"
                gamelog_resp = requests.get(gamelog_url)
                gamelog_data = gamelog_resp.json()

                # Pull season stats
                season_url = f"https://statsapi.mlb.com/api/v1/people/{pitcher['id']}/stats?stats=season&group=pitching"
                season_resp = requests.get(season_url).json()
                stats = season_resp.get("stats", [])
                splits = stats[0].get("splits", []) if stats else []
                season_stats = splits[0].get("stat", {}) if splits else {}
                
                era = season_stats.get("era", "")
                baa = season_stats.get("avg", "")
                opsa = season_stats.get("ops", "")
                
                stats = gamelog_data.get("stats", [])
                splits = stats[0].get("splits", []) if stats else []
                games = splits[:5]

                total_ip = total_er = total_so = 0
                for g in games:
                    stat = g["stat"]
                    total_ip += float(stat.get("inningsPitched", 0))
                    total_er += int(stat.get("earnedRuns", 0))
                    total_so += int(stat.get("strikeOuts", 0))

                rows.append({
                    "Date": game["gameDate"][:10],
                    "Team": team,
                    "Opponent": opp,
                    "Pitcher Name": pitcher["fullName"],
                    "MLB ID": pitcher["id"],
                    "Throws": get_throwing_hand(pitcher["id"]),
                    "Last 5 IP": total_ip,
                    "Last 5 ER": total_er,
                    "Last 5 SO": total_so,
                    "ERA": era,
                    "BAA": baa,
                    "OPSa": opsa
                })
                print(f"✔ {pitcher['fullName']} for {team}")

df = pd.DataFrame(rows)
df.to_csv("latest_pitchers.csv", index=False)
print(f"✅ Saved {len(rows)} pitchers to latest_pitchers.csv")

import subprocess
import datetime

def git_push_csv(file_path):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Update latest_pitchers.csv ({timestamp})"

    try:
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ latest_pitchers.csv pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print("❌ Git push failed:", e)

# Call it at the end of your script
git_push_csv("latest_pitchers.csv")
