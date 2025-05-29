import statsapi
import pandas as pd
from datetime import datetime, timedelta

# ✅ Get today and tomorrow's dates
today = datetime.today()
tomorrow = today + timedelta(days=1)

start = today.strftime('%Y-%m-%d')
end = tomorrow.strftime('%Y-%m-%d')

print(f"📅 Getting games from {start} to {end}")

# ✅ Get schedule with probable pitchers
games = statsapi.schedule(start_date=start, end_date=end, sportId=1, hydrate='probablePitcher')
print(f"⚾ Found {len(games)} games")

rows = []

# ✅ Extract pitcher data
for game in games:
    for side in ['home', 'away']:
        pitcher = game.get(f'{side}ProbablePitcher')
        if pitcher:
            rows.append({
                'Date': game['gameDate'][:10],
                'Team': game[f'{side}Name'],
                'Opponent': game['awayName'] if side == 'home' else game['homeName'],
                'Pitcher Name': pitcher['fullName'],
                'MLB ID': pitcher['id']
            })
            print(f"✔ {pitcher['fullName']} for {game[f'{side}Name']}")

# ✅ Save to CSV
df = pd.DataFrame(rows)
df.to_csv('latest_pitchers.csv', index=False)
print(f"✅ Saved {len(rows)} pitchers to latest_pitchers.csv")
