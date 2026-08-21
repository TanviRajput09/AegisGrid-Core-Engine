# AegisGrid Core Software Engine

 ## Architecture Overview 

The AegisGrid software engine processes 11kV grid electrical signals to perform real-time fault detection, wavelet-based distance estimation, and automated switch control.

 ## Software Pipeline Workflow 

1. Input Data Stream (`/data`) -> 
2. Signal Preprocessing & Wavelet Engine (`/engine`) ->
 3. Fault Classification (`/classifier`) -> 
4. Output Processing & GUI (`/dashboard`) 



 # main.py - AegisGrid Master Engine Pipeline 
import numpy as np 
import pandas as pd 

def run_aegisgrid_engine(input_csv_path): 
print("[INFO] Loading 11kV Grid Data Stream...")
# Step 1: Read Input Data
grid_data = pd.read_csv(input_csv_path)
# Step 2: Pass data to Wavelet Engine (Saleem's Module) 
# distance = calculate_fault_distance(grid_data) 

# Step 3: Pass data to Fault Classifier (Aryan's Module) 
# fault_type = classify_fault_type(grid_data) 

# Step 4: Format Final Output JSON for Dashboard 
output = { 
"status": "Fault Detected",
"fault_type": "Line-to-Ground (L-G)",
"distance_km": 3.42, "loto_relay_state": "TRIPPED"
} 
return output


if __name__ == "__main__":
result = run_aegisgrid_engine("data/sample_11kv_transient.csv")
print("[ENGINE OUTPUT]:", result)