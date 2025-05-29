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
            for team_type in ["away", "home"]:
                team_info = game.get("teams", {}).get(team_type, {})
                pitcher = team_info.get("probablePitcher")
                if pitcher:
                    pitchers.append({
                        "name": pitcher.get("fullName"),
                        "id": pitcher.get("id"),
                        "team": team_info.get("team", {}).get("name"),
                        "opponent": game.get("teams", {}).get("home" if team_type == "away" else "away", {}).get("team", {}).get("name"),
                        "game_date": game.get("gameDate")
                    })
    return pitchers

def get_pitcher_game_logs(pitcher_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "pitching",
        "limit": 5,
        "gameType": "R"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("stats", [{}])[0].get("splits", [])

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    pitchers = get_probable_pitchers(today)
    all_data = []

    for pitcher in pitchers:
        print(f"Processing {pitcher['name']} ({pitcher['team']} vs {pitcher['opponent']})")
        logs = get_pitcher_game_logs(pitcher["id"])
        time.sleep(0.5)  # To respect API rate limits

        for game in logs:
            stats = game.get("stat", {})
            all_data.append({
                "pitcher_name": pitcher["name"],
                "team": pitcher["team"],
                "opponent": pitcher["opponent"],
                "game_date": pitcher["game_date"],
                "log_date": game.get("date"),
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
    df.to_csv("probable_pitcher_game_logs.csv", index=False)
    print(f"Saved {len(df)} records to probable_pitcher_game_logs.csv")

if __name__ == "__main__":
    main()
