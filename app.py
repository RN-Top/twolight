"""Twolight — a clock of the two lights.

The sun rules the day, the moon rules the night.
The moon is shared by everyone on Earth; the sun is your own.
"""
from pathlib import Path
import time

import streamlit as st
import streamlit.components.v1 as components

from moon_engine import moon_state

st.set_page_config(page_title="Twolight", page_icon="🌙", layout="centered")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Jost:wght@300;400&display=swap');
      .stApp { background: #05071A; }
      html, body, [class*="css"] { font-family: 'Jost', system-ui, sans-serif; }
      header[data-testid="stHeader"] { background: transparent; }
      .block-container { padding-top: 1.2rem; max-width: 680px; }
      h1.title { color: #ECE7DA; font-weight: 300; font-size: 1.9rem; text-align: center;
                 letter-spacing: .04em; margin: 0 0 .2rem 0; }
      p.tag { color: #9CC3D3; opacity: .75; text-align: center; font-weight: 300; margin: 0 0 .6rem 0; }
    </style>
    <h1 class="title">Twolight</h1>
    <p class="tag">One moon over the whole world. Your own sun where you stand.</p>
    """,
    unsafe_allow_html=True,
)

face = (Path(__file__).parent / "face.html").read_text(encoding="utf-8")
# Hand the face this server's clock (synced to atomic time) so phones with drifting clocks stay exact.
face = face.replace("__SERVER_MS__", str(int(time.time() * 1000)))
components.html(face, height=880, scrolling=False)

s = moon_state()
with st.expander("The numbers behind the face"):
    h, m, sec = s["moon_hms"]
    st.write(f"**Twolight time:** moon-day {s['moon_day']:02d}, {h:02d}:{m:02d}:{sec:02d} "
             f"(year {s['year']} of 19, moon {s['metonic_moon']} of 235)")
    st.write(f"**Phase:** {s['phase_name']} — {s['illumination'] * 100:.0f}% lit")
    st.write(f"**Day of this moon:** {s['age_days']:.1f} of 29.5")
    st.write(f"**Moon in the 19-year wheel:** {s['metonic_moon']} of 235 (year {s['metonic_year']} of 19)")
    st.write(f"**Shared moment (UTC):** {s['utc']:%Y-%m-%d %H:%M}")
    st.caption(
        "The moon's phase is the same everywhere on Earth at once — that is the shared layer. "
        "The sun on the outer ring follows your own day: allow location for your true sun, "
        "otherwise it follows your device clock."
    )
