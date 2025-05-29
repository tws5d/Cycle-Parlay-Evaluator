import statsapi
import pandas as pd
from datetime import datetime, timedelta

# Set up date range
today = datetime.today()
tomorrow = today + timedelta(days=1)

start = today.strftime('%Y-%m-%d')
end = tomorrow.strftime('%Y-%m-%d')

# Get schedule with probable pitchers
games = statsapi.schedule(start_date=start, end_date=end, sportId=1, hydrate='probablePitcher')

rows = []
for game in games:
    for team_type in ['home', 'away']:
        pitcher = game.get(f'{team_type}ProbablePitcher')
        if pitcher:
            rows.append({
                'Date': game['gameDate'][:10],
                'Team': game[f'{team_type}Name'],
                'Opponent': game[f'{"away" if team_type == "home" else "home"}Name'],
                'Pitcher Name': pitcher['fullName'],
                'MLB ID': pitcher['id']
            })

# Save to CSV
df = pd.DataFrame(rows)
df.to_csv('probable_pitchers.csv', index=False)
print("✅ Saved probable_pitchers.csv")
