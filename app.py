import streamlit as st
from pybaseball import statcast_batter
import pandas as pd
from datetime import datetime, timedelta
from pybaseball import schedule_and_record

st.title("The Cycle Evaluator")

st.markdown("""
Enter a hitter's name to pull recent Statcast data and generate a matchup score based on current form and conditions.
""")

player_name = st.text_input("Enter hitter name (e.g. Juan Soto)")

# Manual pitcher input (since schedule lookup is unreliable)
pitcher_name = st.text_input("Enter opposing pitcher's name (e.g. Zack Wheeler)")

# Define basic player lookup dictionary for testing (add more later)
player_ids = {
    "Juan Soto": 665742,
    "Mookie Betts": 605141,
    "Aaron Judge": 592450,
    "Bryce Harper": 547180,
}

player_teams = {
    "Juan Soto": "NYM",
    "Mookie Betts": "LAD",
    "Aaron Judge": "NYY",
    "Bryce Harper": "PHI",
}

if player_name in player_ids:
    batter_id = player_ids[player_name]
   
    if pitcher_name:
        st.write(f"🧱 Probable Pitcher: {pitcher_name}")
        
    # Get last 14 days of data
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    
    st.write(f"📅 Date range: {start_date} → {end_date}")
    
    df = statcast_batter(start_date, end_date, batter_id)
    
    if not df.empty:
        # Compute xBA and Hard Hit % from available data
        avg_exit_velo = df['launch_speed'].mean()
        hard_hits = df[df['launch_speed'] >= 95].shape[0]
        total_batted_balls = df.shape[0]
        hard_hit_pct = round((hard_hits / total_batted_balls) * 100, 2) if total_batted_balls else 0
        xba = round(df['estimated_ba_using_speedangle'].mean(), 3)

        # Display results
        st.write(f"**Average Exit Velocity:** {round(avg_exit_velo, 1)} mph")
        st.write(f"**Hard Hit %:** {hard_hit_pct}%")
        st.write(f"**xBA (Expected BA):** {xba}")

        # Basic score logic
        score = 50
        if xba > 0.300: score += 15
        if hard_hit_pct > 45: score += 15
        if avg_exit_velo > 91: score += 10

        st.write(f"🧠 **Cycle Score**: {score}/100")
        if score >= 85:
            st.success("🔥 LOCK")
        elif score >= 70:
            st.info("✅ Lean")
        else:
            st.warning("⚠️ Fade")
    else:
        st.warning("No Statcast data found for this timeframe.")
        
elif player_name:
    st.error("Player not found. Try one of: " + ", ".join(player_ids.keys()))
