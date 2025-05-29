# import os
# from datetime import datetime

# def log_event(message):
#     os.makedirs("logs", exist_ok=True)
#     log_path = os.path.join("logs", "events.log")
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     full_message = f"[{timestamp}] {message}"
#     print(full_message)
#     with open(log_path, "a") as f:
#         f.write(full_message + "\n")

import os
import time
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "distributed_sorting.log")

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def log_event(message):
    """
    Log an event with timestamp to the log file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    print(log_message)
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")