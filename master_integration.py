# master_integration.py
# AegisGrid - Module 5: Master Integration & Async Non-Blocking SHA-256 Logger

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

    def generate_iec61850_telemetry_payload(self, pipeline_data, distance_data, protection_data):
        utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload = {
            "header": {
                "system_id": "AEGISGRID_11KV_PROTECTION",
                "substation_id": "SUB_11KV_NORTH",
                "feeder_id": "FDR_04",
                "timestamp_utc": utc_timestamp,
                "data_quality": pipeline_data.get("quality_flag", "GOOD") if pipeline_data else "GOOD"
            },
            "iec61850_logical_nodes": {
                "XCBR1_CircuitBreaker": {
                    "breaker_status": protection_data.get("recloser_state", "HEALTHY"),
                    "loto_engaged": protection_data.get("loto_active", False),
                    "action_taken": protection_data.get("protection_action", "NO_ACTION")
                },
                "MMXU1_Measurements": {
                    "volts_kv": pipeline_data['metrics']['primary'].get('v_primary_kv', pipeline_data['metrics']['primary'].get('voltage_kv', 11.0)) if (pipeline_data and 'metrics' in pipeline_data and 'primary' in pipeline_data['metrics']) else 11.0,
                    "primary_current_a": pipeline_data['metrics']['primary']['current_a'] if pipeline_data else 0.0,
                    "ct_pt_ratio": pipeline_data['metrics']['ratios_applied'] if pipeline_data else "N/A"
                },
                "PTOC1_Protection": {
                    "fault_type": protection_data.get("fault_type", "NORMAL"),
                    "directional_flag": distance_data.get("directional_flag", "FORWARD_FAULT"),
                    "calculated_distance_km": distance_data.get("fault_distance_km", 0.0),
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
