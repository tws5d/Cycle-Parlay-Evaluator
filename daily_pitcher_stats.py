import statsapi
from datetime import datetime, timedelta

# Dates
today = datetime.today()
tomorrow = today + timedelta(days=1)

start = today.strftime('%Y-%m-%d')
end = tomorrow.strftime('%Y-%m-%d')

# Get schedule
games = statsapi.schedule(start_date=start, end_date=end, sportId=1, hydrate='probablePitcher')

print(f"Found {len(games)} games")
for game in games:
    print("Game:", game['gameDate'][:10], game['awayName'], "at", game['homeName'])
    for side in ['home', 'away']:
        pitcher = game.get(f'{side}ProbablePitcher')
        if pitcher:
            print(f"{side.title()} pitcher: {pitcher['fullName']} (ID: {pitcher['id']})")
        else:
            print(f"No probable {side} pitcher listed.")
