import requests
import pandas as pd
from datetime import datetime, timedelta

today = datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

# MLB Schedule endpoint
url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={today}&endDate={tomorrow}&hydrate=probablePitcher"

response = requests.get(url)
data = response.json()
import json
print(json.dumps(data, indent=2)[:2000])  # limit output to first 2000 characters

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

                games = gamelog_data.get("stats", [{}])[0].get("splits", [])[:5]

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
                    "Last 5 IP": total_ip,
                    "Last 5 ER": total_er,
                    "Last 5 SO": total_so
                })
                print(f"✔ {pitcher['fullName']} for {team}")

df = pd.DataFrame(rows)
df.to_csv("latest_pitchers.csv", index=False)
print(f"✅ Saved {len(rows)} pitchers to latest_pitchers.csv")
