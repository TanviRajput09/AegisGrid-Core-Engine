# main.py - AegisGrid Master Integration, IEC 61850 Telemetry & SHA-256 Audit Logger
# Lead: Tanvi

import os
import json
import datetime
import hashlib
import queue
import threading
import time

class SCADAMasterIntegrationEngine:
    def __init__(self, log_filename="scada_audit_chained.log"):
        self.log_filename = log_filename
        self.last_log_hash = "0" * 64  # Initial Genesis Hash for Blockchain-style chaining
        
        # In-Memory Ring Buffer (Queue) & Async Worker Setup to prevent UI lockup
        self.log_queue = queue.Queue(maxsize=1000)
        self.worker_thread = threading.Thread(target=self._async_log_writer, daemon=True)
        self.worker_thread.start()

    def generate_iec61850_telemetry_payload(self, pipeline_data=None, distance_data=None, protection_data=None):
        """
        Formats backend outputs into standardized IEC 61850 Logical Node telemetry schema:
        - XCBR: Circuit Breaker Logical Node
        - MMXU: Measurement Logical Node
        - PTOC: Protection Logical Node
        """
        pipeline_data = pipeline_data or {}
        distance_data = distance_data or {}
        protection_data = protection_data or {}

        utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        metrics = pipeline_data.get('metrics', {})
        primary = metrics.get('primary', {})
        secondary = metrics.get('secondary', {})

        v_primary_kv = primary.get('voltage_kv', 11.0)
        i_primary_a = primary.get('current_a', 0.0)

        v_secondary_v = secondary.get('voltage_v', 110.0)
        i_secondary_a = secondary.get('current_a', 0.0)

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
                    "primary_volts_kv": v_primary_kv,
                    "primary_current_a": i_primary_a,
                    "secondary_volts_v": v_secondary_v,
                    "secondary_current_a": i_secondary_a,
                    "ct_pt_ratio": metrics.get('ratios_applied', "N/A")
                },
                "PTOC1_Protection": {
                    "fault_type": protection_data.get("fault_type", "NORMAL"),
                    "directional_flag": distance_data.get("directional_flag", "FORWARD_FAULT"),
                    "calculated_distance_km": distance_data.get("fault_distance_km", 0.0),
                    "distance_method": distance_data.get("method_used", "NONE"),
                    "status_detail": protection_data.get("status_message", "Operational")
                }
            }
        }

        # Non-blocking async queue insertion
        self.append_chained_audit_log(payload)
        return payload

    def append_chained_audit_log(self, payload_dict):
        """
        Pushes telemetry record to in-memory queue to prevent file I/O lockup.
        """
        try:
            raw_data_string = json.dumps(payload_dict, sort_keys=True)
            combined_payload = raw_data_string + self.last_log_hash
            current_entry_hash = hashlib.sha256(combined_payload.encode('utf-8')).hexdigest()

            audit_record = {
                "telemetry_data": payload_dict,
                "audit_security": {
                    "previous_hash": self.last_log_hash,
                    "entry_hash": current_entry_hash
                }
            }

            # Push to queue without blocking
            if not self.log_queue.full():
                self.log_queue.put(audit_record)
            
            # Update hash chain state immediately
            self.last_log_hash = current_entry_hash
            return current_entry_hash

        except Exception as e:
            print(f"[SECURE AUDIT ERROR] Could not buffer audit record: {e}")
            return None

    def _async_log_writer(self):
        """
        Background worker thread processing log queue asynchronously.
        """
        while True:
            try:
                record = self.log_queue.get()
                with open(self.log_filename, "a") as log_file:
                    log_file.write(json.dumps(record) + "\n")
                self.log_queue.task_done()
            except Exception as e:
                print(f"[ASYNC WORKER ERROR] Failed writing to log file: {e}")
            time.sleep(0.01)

def run_aegisgrid_pipeline():
    print("⚡ [INFO] Starting AegisGrid IEC 61850 SCADA Master Engine (Async Audit Enabled)...")
    integrator = SCADAMasterIntegrationEngine()
    
    mock_pipeline = {
        "quality_flag": "GOOD",
        "metrics": {
            "primary": {"voltage_kv": 11.0, "current_a": 480.0},
            "secondary": {"voltage_v": 110.0, "current_a": 1.2},
            "ratios_applied": "CT(400:1), PT(100:1)"
        }
    }
    mock_distance = {
        "fault_distance_km": 4.35,
        "directional_flag": "FORWARD_FAULT",
        "method_used": "HYBRID_WAVELET_IMPEDANCE"
    }
    mock_protection = {
        "protection_action": "HARD_TRIP_LOTO",
        "fault_type": "L-G (Phase A)",
        "recloser_state": "LOCKOUT",
        "loto_active": True,
        "status_message": "Permanent L-G Fault - Breaker Locked Out"
    }

    final_payload = integrator.generate_iec61850_telemetry_payload(mock_pipeline, mock_distance, mock_protection)
    print("⚡ [INFO] Telemetry Payload Generated & Pushed to Async Audit Queue.")

    print("⚡ [INFO] Launching Control Room Dashboard UI...")
    os.system("streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    run_aegisgrid_pipeline()
