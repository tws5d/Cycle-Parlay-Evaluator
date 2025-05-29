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
    if not table:
        print("❌ Could not find the pitchers table on Rotowire.")
        return []

    tbody = table.find("tbody")
    if not tbody:
        print("❌ No table body found.")
        return []

    rows = tbody.find_all("tr")
    print(f"✅ Found {len(rows)} rows in table.")

    names = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        away = cells[2].text.strip()
        home = cells[4].text.strip()
        names.extend([away, home])
    
    unique_names = list(set(names))
    print(f"✅ Extracted {len(unique_names)} unique pitcher names.")
    return unique_names

def get_mlb_id(name):
    parts = name.replace(".", "").split()
    if len(parts) < 2:
        print(f"⚠️ Not enough parts in name: {name}")
        return None
    first, last = parts[0], parts[-1]
    print(f"🔍 Looking up: first={first}, last={last}")
    try:
        df = playerid_lookup(last, fir_
