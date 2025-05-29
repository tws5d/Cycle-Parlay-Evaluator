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
   
    from pybaseball import playerid_lookup, statcast_pitcher

    if pitcher_name:
        st.write(f"🧱 Probable Pitcher: {pitcher_name}")

        # Lookup pitcher ID from name
        try:
            pitcher_lookup = playerid_lookup(*pitcher_name.split())
            pitcher_id = int(pitcher_lookup.iloc[0]['key_mlbam'])
        
            # Get last 14 days of Statcast data for pitcher
            df_pitcher = statcast_pitcher(start_date, end_date, pitcher_id)

            if not df_pitcher.empty:
                # Calculate allowed contact metrics
                avg_ev_allowed = df_pitcher['launch_speed'].mean()
                hard_hits_allowed = df_pitcher[df_pitcher['launch_speed'] >= 95].shape[0]
                total_contact = df_pitcher.shape[0]
                hard_hit_pct_allowed = round((hard_hits_allowed / total_contact) * 100, 2) if total_contact else 0
                xba_allowed = round(df_pitcher['estimated_ba_using_speedangle'].mean(), 3)

                st.write(f"📉 **Pitcher xBA Allowed:** {xba_allowed}")
                st.write(f"📉 **Hard Hit % Allowed:** {hard_hit_pct_allowed}%")
                st.write(f"📉 **Avg Exit Velo Allowed:** {round(avg_ev_allowed, 1)} mph")

                # Adjust Cycle Score based on pitcher weakness
                if xba_allowed > 0.280: score += 10
                if hard_hit_pct_allowed > 40: score += 10
                if avg_ev_allowed > 89: score += 5
            
            else:
                st.warning("No recent data for pitcher.")

            except:
                st.warning("Pitcher lookup failed. Check spelling.")
  
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
