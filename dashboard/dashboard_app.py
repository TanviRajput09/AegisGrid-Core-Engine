# dashboard/dashboard_app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

# Import Classifier Bridge JSON output
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
from pathlib import Path

# Add project root directory to sys.path dynamically
sys.path.append(str(Path(__file__).resolve().parent.parent))

from CLASSIFIER.classifier_bridge import get_fault_classification_payload

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(page_title="AegisGrid Control Room", page_icon="⚡", layout="wide")

st.title("⚡ AegisGrid: 11kV Smart Grid Fault Locator & Protection System")
st.markdown("---")

# --------------------------------------------------
# SIDEBAR CONTROL PANEL
# --------------------------------------------------
st.sidebar.header("🔧 Grid Control Panel")
input_file = st.sidebar.file_uploader("Upload 11kV Sensor CSV Data", type=["csv"])
run_btn = st.sidebar.button("▶ Run Fault Detection Engine", use_container_width=True)

# --------------------------------------------------
# BACKEND JSON PAYLOAD INGESTION
# --------------------------------------------------
payload = get_fault_classification_payload()
fault_dist_km = payload.get("distance_km", 3.42)
fault_type = payload.get("fault_type", "Line-to-Ground (L-G)")
loto_status = payload.get("loto_relay_state", "TRIPPED")
tools = payload.get("tools_required", [])
ppe_items = payload.get("ppe_safety", [])

# Demo Sensor Data Setup
t = np.linspace(0, 0.1, 1000)
current = 100 * np.sin(2 * np.pi * 50 * t)
current[200:210] = [250, 300, 350, 400, 450, 380, 320, 280, 220, 180]
voltage = np.ones(1000) * 11000

sensor_data = pd.DataFrame({"Time (s)": t, "Voltage (V)": voltage, "Current (A)": current})

if input_file is not None:
    try:
        sensor_data = pd.read_csv(input_file)
        st.sidebar.success("✅ CSV Data Loaded Successfully")
    except Exception as e:
        st.sidebar.error(f"CSV Error: {e}")

# --------------------------------------------------
# RUN DASHBOARD DISPLAY
# --------------------------------------------------
if run_btn or input_file is not None:

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⚡ Grid Voltage", "11.0 kV", "Normal")
    col2.metric("📍 Fault Distance", f"{fault_dist_km} km", delta_color="inverse")
    col3.metric("🚨 Fault Classification", fault_type)
    col4.metric("🔒 LOTO Safety Relay", loto_status, delta_color="inverse")

    st.markdown("---")

    st.subheader("📍 11kV Feeder Fault Distance Map")
    progress_val = int((fault_dist_km / 10.0) * 100)
    st.write(f"🏭 Substation [0.0 km] ━━━━━━━━━━━━ ⚠️ Fault [{fault_dist_km} km] ━━━━━━━━━━━━ 🔚 Feeder End [10.0 km]")
    st.progress(progress_val)

    st.markdown("---")

    st.subheader(f"⚠️ FAULT AT {fault_dist_km} KM — Live Transient Current Signal")
    fig = px.line(sensor_data, x="Time (s)" if "Time (s)" in sensor_data.columns else sensor_data.columns[0],
                  y="Current (A)" if "Current (A)" in sensor_data.columns else sensor_data.columns[-1],
                  title="High-Frequency Transient Peak Detection")
    fig.update_layout(height=400, xaxis_title="Time (seconds)", yaxis_title="Current (A)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🛡️ Safety Protocols & Tools Required")
    scol1, scol2 = st.columns(2)
    with scol1:
        st.markdown("**🔧 Required Tools:**")
        for tool in tools:
            st.write(f"- {tool}")
    with scol2:
        st.markdown("**🥽 Required PPE Gear:**")
        for ppe in ppe_items:
            st.write(f"- {ppe}")

else:
    st.info("👈 Click **▶ Run Fault Detection Engine** to view dashboard analytics.")
  
