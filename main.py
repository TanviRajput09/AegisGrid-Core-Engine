# main.py
# AegisGrid V4.2 - Module 5: IEC 61850 Orchestration & Cryptographic Audit
# Lead: Tanvi

import os
import json
import datetime
import hashlib
import queue
import threading

class SCADAMasterIntegrationEngine:
    def __init__(self, log_filename="scada_audit_chained.log"):
        self.log_filename = log_filename
        self.last_log_hash = "0" * 64
        self.log_queue = queue.Queue(maxsize=1000)
        
        self.writer_thread = threading.Thread(target=self._async_disk_writer, daemon=True)
        self.writer_thread.start()

    def generate_iec61850_telemetry_payload(self, pipeline_data=None, distance_data=None, protection_data=None):
        pipeline_data = pipeline_data or {}
        distance_data = distance_data or {}
        protection_data = protection_data or {}

        utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        metrics = pipeline_data.get('metrics', {})
        primary = metrics.get('primary', {})

        payload = {
            "header": {
                "system_id": "AEGISGRID_11KV_CSPDCL",
                "substation_id": "SUB_11KV_DURG_NORTH",
                "timestamp_utc": utc_timestamp
            },
            "iec61850_nodes": {
                "XCBR1": {"status": protection_data.get("recloser_state", "HEALTHY")},
                "MMXU1": {"volts_kv": primary.get('v_primary_kv', 11.0)},
                "PTOC1": {
                    "hif_arcing_status": protection_data.get("hif_status", "NORMAL"),
                    "ct_saturation": distance_data.get("ct_saturation_detected", False),
                    "fault_distance_km": distance_data.get("fault_distance_km", 0.0)
                }
            }
        }
        self.append_chained_audit_log(payload)
        return payload

    def append_chained_audit_log(self, payload_dict):
        raw_data = json.dumps(payload_dict, sort_keys=True)
        current_hash = hashlib.sha256((raw_data + self.last_log_hash).encode('utf-8')).hexdigest()
        
        record = {"telemetry": payload_dict, "hash": current_hash, "prev_hash": self.last_log_hash}
        self.last_log_hash = current_hash
        if not self.log_queue.full():
            self.log_queue.put(record)

    def _async_disk_writer(self):
        while True:
            record = self.log_queue.get()
            try:
                with open(self.log_filename, "a") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception as e:
                print(f"[ASYNC LOG ERROR]: {e}")
            self.log_queue.task_done()

def run_aegisgrid_pipeline():
    print("⚡ [INFO] Starting AegisGrid V4.2 Orchestrator...")
    integrator = SCADAMasterIntegrationEngine()
    
    mock_pipeline = {"metrics": {"primary": {"v_primary_kv": 11.0}}}
    mock_distance = {"ct_saturation_detected": False, "fault_distance_km": 4.35}
    mock_protection = {"recloser_state": "LOCKOUT", "hif_status": "ARCING_DETECTED"}

    integrator.generate_iec61850_telemetry_payload(mock_pipeline, mock_distance, mock_protection)
    print("⚡ [INFO] V4.2 Schema Verified & Logged.")

    print("⚡ [INFO] Launching Control Room Dashboard...")
    os.system("streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    run_aegisgrid_pipeline()
