import requests
import pandas as pd
from datetime import datetime, timedelta

today = datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

# MLB Schedule endpoint
url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={today}&endDate={tomorrow}&hydrate=probablePitcher"

response = requests.get(url)
data = response.json()

rows = []

for date in data["dates"]:
    for game in date["games"]:
        for side in ['home', 'away']:
            team = game["teams"][side]["team"]["name"]
            opp = game["teams"]["away"]["team"]["name"] if side == "home" else game["teams"]["home"]["team"]["name"]
            pitcher = game.get(f"{side}ProbablePitcher")
            if pitcher:
                rows.append({
                    "Date": game["gameDate"][:10],
                    "Team": team,
                    "Opponent": opp,
                    "Pitcher Name": pitcher["fullName"],
                    "MLB ID": pitcher["id"]
                })
                print(f"✔ {pitcher['fullName']} for {team}")

df = pd.DataFrame(rows)
df.to_csv("latest_pitchers.csv", index=False)
print(f"✅ Saved {len(rows)} pitchers to latest_pitchers.csv")
