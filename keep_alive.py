"""
keep_alive.py
─────────────────────────────────────────────────────────────────
Lightweight HTTP pinger that hits your Streamlit app URLs every
14 minutes to prevent Streamlit Community Cloud free-tier apps
from going to sleep.

Usage (run locally or on a cheap cron host like Railway / Render):
    python keep_alive.py

Or use the built-in GitHub Actions workflow (see .github/workflows/keep_alive.yml).
─────────────────────────────────────────────────────────────────
"""

import os
import time
import urllib.request
import urllib.error
from datetime import datetime

URLS = [
    os.environ.get("MAIN_APP_URL",      "https://hr-management-systemm.streamlit.app/"),
    os.environ.get("ATTENDANCE_URL",    "https://staff-attendance.streamlit.app/"),
    os.environ.get("BUSINESS_URL",      "https://business-department.streamlit.app/"),
    os.environ.get("STAFF_URL",         "https://staff-performance.streamlit.app/"),
    os.environ.get("ADMIN_URL",         "https://management-panel.streamlit.app/"),
]

INTERVAL_SECONDS = int(os.environ.get("PING_INTERVAL", "840"))  # 14 minutes


def ping(url: str) -> None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KeepAlive/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"[{datetime.now():%H:%M:%S}] ✅ {url} → {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"[{datetime.now():%H:%M:%S}] ⚠️  {url} → HTTP {e.code}")
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ❌ {url} → {e}")


if __name__ == "__main__":
    print(f"Keep-alive started. Pinging every {INTERVAL_SECONDS // 60} minutes.")
    while True:
        for url in URLS:
            ping(url)
        time.sleep(INTERVAL_SECONDS)
