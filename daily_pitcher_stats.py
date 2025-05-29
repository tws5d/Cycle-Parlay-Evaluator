import requests
from bs4 import BeautifulSoup
import pandas as pd
from pybaseball import playerid_lookup
import time

def get_rotowire_probable_pitchers():
    url = "https://www.rotowire.com/baseball/probable-pitchers.php"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", class_="tablesorter")
    rows = table.find("tbody").find_all("tr")

    names = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        away = cells[2].text.strip()
        home = cells[4].text.strip()
        names.extend([away, home])
    return list(set(names))  # Remove duplicates

def get_mlb_id(name):
    parts = name.replace(".", "").split()
    if len(parts) < 2:
        return None
    first, last = parts[0], parts[-1]
    try:
        df = playerid_lookup(last, first)
        if not df.empty:
            return int(df.iloc[0]["key_mlbam"])
    except Exception as e:
        print(f"Lookup error for {name}: {e}")
    return None

def get_pitcher_logs(mlb_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "pitching",
        "limit": 5,
        "gameType": "R"
    }
    r = requests.get(url, params=params).json()
    return r.get("stats", [{}])[0].get("splits", [])

def main():
    names = get_rotowire_probable_pitchers()
    print(f"✅ Found {len(names)} probable pitchers:")
    for name in names:
        print("-", name)
    all_data = []

    for name in names:
        print(f"Processing {name}...")
        mlb_id = get_mlb_id(name)
        print(f"MLB ID for {name}: {mlb_id}")
        time.sleep(0.5)  # To be nice to API

        if not mlb_id:
            print(f"❌ Could not find ID for {name}")
            continue

        logs = get_pitcher_logs(mlb_id)
        if not logs:
            print(f"⚠️ No logs returned for {name} (ID {mlb_id}) — maybe inactive or not started yet.")
            continue


        for game in logs:
            stat = game["stat"]
            all_data.append({
                "pitcher_name": name,
                "mlb_id": mlb_id,
                "date": game.get("date", ""),
                "innings_pitched": stat.get("inningsPitched", "0.0"),
                "earned_runs": stat.get("earnedRuns", 0),
                "strike_outs": stat.get("strikeOuts", 0),
                "walks": stat.get("baseOnBalls", 0),
                "hits": stat.get("hits", 0),
                "pitches": stat.get("numberOfPitches", 0),
                "era": stat.get("era", 0),
                "whip": stat.get("whip", 0)
            })

    df = pd.DataFrame(all_data)
    df.to_csv("probable_pitcher_game_logs.csv", index=False)
    print(f"✅ Saved {len(df)} rows to probable_pitcher_game_logs.csv")

if __name__ == "__main__":
    main()
