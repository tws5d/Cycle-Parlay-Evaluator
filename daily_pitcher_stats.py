import statsapi
import pandas as pd
from datetime import datetime, timedelta

print("🚀 Script is running!", flush=True)

# Dates
today = datetime.today()
tomorrow = today + timedelta(days=1)

start = today.strftime('%Y-%m-%d')
end = tomorrow.strftime('%Y-%m-%d')

print(f"Getting games between {start} and {end}", flush=True)

# Fetch schedule with probable pitchers
games = statsapi.schedule(start_date=start, end_date=end, sportId=1, hydrate='probablePitcher')
print(f"Found {len(games)} games", flush=True)

rows = []
for game in games:
    for side in ['home', 'away']:
        pitcher = game.get(f'{side}ProbablePitcher')
        if pitcher:
            rows.append({
                'Date': game['gameDate'][:10],
                'Team': game[f'{sid]()
