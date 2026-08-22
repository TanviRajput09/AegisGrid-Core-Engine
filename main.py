# main.py - AegisGrid Master Engine Pipeline & Dashboard Launcher
import os
import sys

def run_aegisgrid_engine(input_csv_path=None):
    print("[INFO] Loading 11kV Grid Data Stream...")
    
    # Step 1: Pass data to Wavelet Engine (Saleem's Module)
    # distance = calculate_fault_distance(grid_data)
    
    # Step 2: Pass data to Fault Classifier (Aryan's Module)
    # fault_type = classify_fault_type(grid_data)
    
    # Step 3: Launch Streamlit Dashboard (Yashasvi's UI)
    print("[INFO] Launching Control Room Dashboard...")
    os.system("streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    run_aegisgrid_engine()
    
