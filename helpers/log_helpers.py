from datetime import datetime
import os

# Set up a log file path
LOG_FOLDER = "logs"
LOG_FILE = os.path.join(
    LOG_FOLDER,
    f"run_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

# Create the logs folder if it doesn't exist
os.makedirs(LOG_FOLDER, exist_ok=True)

def log_data(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, "a") as f:
        f.write(full_message + "\n")
