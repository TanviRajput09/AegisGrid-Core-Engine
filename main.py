# main.py
# AegisGrid V4.2 - Master Orchestration Pipeline
# Lead: Tanvi

import os
import pandas as pd
from master_integration import SCADAMasterIntegrationEngine

def run_aegisgrid_pipeline():
    print("⚡ [INFO] Starting AegisGrid V4.2 Master Orchestration Pipeline...")
    
    # Initialize the Module 5 Master Integration Engine
    engine = SCADAMasterIntegrationEngine()
    
    # CSV Data Stream / Pipeline Reader for V4.2
    csv_filepath = "data/sample_11kv_transients.csv"
    
    if os.path.exists(csv_filepath):
        print(f"⚡ [INFO] Loading telemetry data from {csv_filepath}...")
        df = pd.read_csv(csv_filepath)
        
        for index, row in df.iterrows():
            mock_pipeline = {
                "quality_flag": row.get('quality', 'GOOD'),
                "metrics": {
                    "primary": {
                        "v_primary_kv": row.get('voltage_kv', 11.0),
                        "current_a": row.get('current_a', 0.0)
                    },
                    "ratios_applied": row.get('ratio', 'CT(400:1), PT(100:1)')
                }
            }
            mock_distance = {
                "fault_distance_km": row.get('distance_km', 4.35),
                "directional_flag": row.get('direction', 'FORWARD_FAULT'),
                "ct_saturation_detected": bool(row.get('ct_saturation', False))
            }
            mock_protection = {
                "protection_action": row.get('action', 'HARD_TRIP_LOTO'),
                "fault_type": row.get('fault_type', 'L-G (Phase A)'),
                "recloser_state": row.get('recloser_state', 'LOCKOUT'),
                "loto_active": bool(row.get('loto_active', True)),
                "hif_status": row.get('hif_status', 'ARCING_DETECTED'),
                "status_message": row.get('status_msg', 'Permanent Fault - Locked Out')
            }
            
            engine.generate_iec61850_telemetry_payload(mock_pipeline, mock_distance, mock_protection)
            
        print("⚡ [INFO] All CSV telemetry records processed via V4.2 pipeline and async logged.")
        
    else:
        print(f"⚠️ [WARN] {csv_filepath} not found. Executing fallback V4.2 integration payload...")
        mock_pipeline = {
            "quality_flag": "GOOD",
            "metrics": {"primary": {"v_primary_kv": 11.0, "current_a": 480.0}, "ratios_applied": "CT(400:1), PT(100:1)"}
        }
        mock_distance = {"fault_distance_km": 4.35, "directional_flag": "FORWARD_FAULT", "ct_saturation_detected": False}
        mock_protection = {
            "protection_action": "HARD_TRIP_LOTO", "fault_type": "L-G (Phase A)",
            "recloser_state": "LOCKOUT", "loto_active": True, "hif_status": "ARCING_DETECTED",
            "status_message": "Permanent L-G Fault - Breaker Locked Out"
        }
        engine.generate_iec61850_telemetry_payload(mock_pipeline, mock_distance, mock_protection)
        print("⚡ [INFO] Fallback V4.2 payload generated and audit-logged.")

    # Launch Control Room Dashboard UI
    print("⚡ [INFO] Launching Control Room Dashboard UI...")
    os.system("streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    run_aegisgrid_pipeline()
    
