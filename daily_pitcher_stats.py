import requests
import pandas as pd
from datetime import datetime
import time

def get_probable_pitchers(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    response = requests.get(url)
    data = response.json()

    pitchers = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            for side in ["home", "away"]:
                team_data = game.get("teams", {}).get(side, {})
                pitcher = team_data.get("probablePitcher")
                if pitcher:
                    pitchers.append({
                        "name": pitcher.get("fullName", "Unknown"),
                        "id": pitcher.get("id", "N/A"),
                        "team": team_data.get("team", {}).get("name", ""),
                        "opponent": game.get("teams", {}).get("home" if side == "away" else "away", {}).get("team", {}).get("name", ""),
                        "game_time": game.get("gameDate", "")
                    })
    return pitchers

def get_pitcher_logs(mlb_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "pitching",
        "limit": 5,
        "gameType": "R"
    }
    response = requests.get(url, params=params).json()
    return response.get("stats", [{}])[0].get("splits", [])

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    pitchers = get_probable_pitchers(today)

    print(f"\n✅ Found {len(pitchers)} probable pitchers for {today}\n")
    all_data = []

    for pitcher in pitchers:
        print(f"Fetching logs for {pitcher['name']} ({pitcher['team']} vs {pitcher['opponent']})")
        logs = get_pitcher_logs(pitcher["id"])
        time.sleep(0.4)

        for game in logs:
            stats = game.get("stat", {})
            all_data.append({
                "pitcher_name": pitcher["name"],
                "team": pitcher["team"],
                "opponent": pitcher["opponent"],
                "date": game.get("date", ""),
                "innings_pitched": stats.get("inningsPitched"),
                "earned_runs": stats.get("earnedRuns"),
                "strike_outs": stats.get("strikeOuts"),
                "walks": stats.get("baseOnBalls"),
                "hits": stats.get("hits"),
                "pitches": stats.get("numberOfPitches"),
                "era": stats.get("era"),
                "whip": stats.get("whip")
            })

    df = pd.DataFrame(all_data)
    df.to_csv("probable_pitchers_stats.csv", index=False)
    print(f"\n✅ Saved {len(df)} rows to probable_pitchers_stats.csv")

if __name__ == "__main__":
    main()
