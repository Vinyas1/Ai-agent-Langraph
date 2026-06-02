"""
JSON logger — writes each agent run's full history for demo transcripts.
"""

import json
import os
from datetime import datetime

LOG_DIR = "logs"


def save_run_log(final_state: dict) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_type = final_state.get("task_type", "unknown")
    filename = f"{LOG_DIR}/run_{task_type}_{timestamp}.json"

    log_data = {
        "timestamp": timestamp,
        "task_type": task_type,
        "goal": final_state.get("goal", ""),
        "dataset_path": final_state.get("dataset_path", ""),
        "total_attempts": final_state.get("attempts", 0),
        "passed": final_state.get("passed", False),
        "final_metrics": final_state.get("metrics", ""),
        "final_code": final_state.get("code", ""),
        "dataset_info": final_state.get("dataset_info", ""),
        "history": final_state.get("history", []),
    }

    with open(filename, "w") as f:
        json.dump(log_data, f, indent=2)

    return filename
