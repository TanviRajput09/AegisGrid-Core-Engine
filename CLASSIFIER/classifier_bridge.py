# classifier/classifier_bridge.py

def get_fault_classification_payload():
    """
    Module contract for classifier payload ingestion by Dashboard.
    Includes fault classification, distance estimation, required tools, and safety protocols.
    """
    payload = {
        "status": "Fault Detected",
        "fault_type": "Line-to-Ground (L-G)",
        "distance_km": 3.42,
        "loto_relay_state": "TRIPPED",
        "tools_required": [
            "Insulated Torque Wrench",
            "High-Voltage Multi-Meter",
            "Grounding Rod Set"
        ],
        "ppe_safety": [
            "Class 4 Arc Flash Suit",
            "17kV Electrical Dielectric Gloves",
            "Insulated Safety Boots"
        ]
    }
    return payload