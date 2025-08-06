# main.py
import threading
import uvicorn
from server import app, server
from gui import launch_gui

def run_api():
    uvicorn.run("server:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    server.parse_config()
    t = threading.Thread(target=run_api, daemon=True)
    t.start()

    launch_gui()