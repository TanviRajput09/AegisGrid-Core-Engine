# main.py
# AegisGrid - Module 5: Master Integration, Arc-HIF State, CT Saturation & Async SHA-256 Logger
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
        
        # Async background writer thread (Prevents file I/O thread lock)
        self.writer_thread = threading.Thread(target=self._async_disk_writer, daemon=True)
        self.writer_thread.start()

    def generate_iec61850_telemetry_payload(self, pipeline_data=None, distance_data=None, protection_data=None, arc_hif_data=None, ct_saturation_data=None):
        pipeline_data = pipeline_data or {}
        distance_data = distance_data or {}
        protection_data = protection_data or {}
        arc_hif_data = arc_hif_data or {}
        ct_saturation_data = ct_saturation_data or {}

        utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        metrics = pipeline_data.get('metrics', {})
        primary = metrics.get('primary', {})

        payload = {
            "header": {
                "system_id": "AEGISGRID_11KV_PROTECTION",
                "substation_id": "SUB_11KV_NORTH",
                "feeder_id": "FDR_04",
                "timestamp_utc": utc_timestamp,
                "data_quality": pipeline_data.get("quality_flag", "GOOD")
            },
            "iec61850_logical_nodes": {
                "XCBR1_CircuitBreaker": {
                    "breaker_status": protection_data.get("recloser_state", "HEALTHY"),
                    "loto_engaged": protection_data.get("loto_active", False),
                    "action_taken": protection_data.get("protection_action", "NO_ACTION")
                },
                "MMXU1_Measurements": {
                    "primary_volts_kv": primary.get('voltage_kv', 11.0),
                    "primary_current_a": primary.get('current_a', 0.0),
                    "ct_saturation_flag": ct_saturation_data.get("is_saturated", False),
                    "ct_saturation_ratio": ct_saturation_data.get("saturation_ratio", 1.0),
                    "ct_pt_ratio": metrics.get('ratios_applied', "N/A")
                },
                "PTOC1_Protection": {
                    "fault_type": protection_data.get("fault_type", "NORMAL"),
                    "directional_flag": distance_data.get("directional_flag", "FORWARD_FAULT"),
                    "calculated_distance_km": distance_data.get("fault_distance_km", 0.0),
                    "arc_hif_detected": arc_hif_data.get("hif_detected", False),
                    "arcing_severity_score": arc_hif_data.get("severity_score", 0.0),
                    "status_detail": protection_data.get("status_message", "Operational")
                }
            }
        }
        self.append_chained_audit_log(payload)
        return payload

    def append_chained_audit_log(self, payload_dict):
        raw_data = json.dumps(payload_dict, sort_keys=True)
        combined = raw_data + self.last_log_hash
        current_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        audit_record = {
            "telemetry_data": payload_dict,
            "audit_security": {"previous_hash": self.last_log_hash, "entry_hash": current_hash}
        }
        self.last_log_hash = current_hash
        
        # Non-blocking memory push
        if not self.log_queue.full():
            self.log_queue.put(audit_record)

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
    print("⚡ [INFO] Starting AegisGrid IEC 61850 Master Engine (Arc-HIF & CT Saturation Synced)...")
    integrator = SCADAMasterIntegrationEngine()
    
    # Verification Run with synced parameters
    mock_pipeline = {
        "quality_flag": "GOOD",
        "metrics": {
            "primary": {"voltage_kv": 11.0, "current_a": 480.0},
            "ratios_applied": "CT(400:1), PT(100:1)"
        }
    }
    mock_distance = {
        "fault_distance_km": 4.35,
        "directional_flag": "FORWARD_FAULT"
    }
    mock_protection = {
        "protection_action": "HARD_TRIP_LOTO",
        "fault_type": "L-G (Phase A)",
        "recloser_state": "LOCKOUT",
        "loto_active": True,
        "status_message": "Permanent L-G Fault - Breaker Locked Out"
    }
    mock_arc_hif = {
        "hif_detected": True,
        "severity_score": 88.5
    }
    mock_ct_sat = {
        "is_saturated": False,
        "saturation_ratio": 1.02
    }

    final_payload = integrator.generate_iec61850_telemetry_payload(
        mock_pipeline, mock_distance, mock_protection, mock_arc_hif, mock_ct_sat
    )
    print("⚡ [INFO] Fully Synced Telemetry Payload Generated & Queued.")

    print("⚡ [INFO] Launching Dashboard...")
    os.system("streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    run_aegisgrid_pipeline()
