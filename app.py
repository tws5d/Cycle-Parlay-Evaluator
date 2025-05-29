import streamlit as st

# App title
st.title("The Cycle Evaluator")

st.markdown("""
This app helps you evaluate if a hitter is a strong prop play today based on BvP, recent form, pitcher quality, and environmental factors.
""")

# Player input
player_name = st.text_input("Enter player name (e.g. Juan Soto)")

# Placeholder scoring logic
if player_name:
    st.subheader(f"Evaluating: {player_name}")
    score = 78  # Placeholder until we connect live data
    
    st.write(f"🧠 **Cycle Score**: {score}/100")
    
    if score >= 85:
        st.success("🔥 LOCK – Ideal play for your prop cycle.")
    elif score >= 70:
        st.info("✅ Lean – Solid option, worth considering.")
    else:
        st.warning("⚠️ Fade – May not be the right spot today.")
