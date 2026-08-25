"""
utils/logger.py — structured, worker-safe logging for CPaaS+ automation.

Every log line carries: timestamp, environment, channel, test name, worker
ID, a test-data/correlation ID, and status/level — so a campaign ID, message
ID, or DLR callback surfaced in the live app can be traced back to the exact
parallel worker and test that produced it.

Writes to stderr (visible in `pytest -s` / CI logs) AND to a per-worker JSON
Lines file under reports/logs/<worker>.jsonl, so a run with many parallel
workers doesn't interleave unreadable output on one shared stream — each
worker's full structured history is in its own file, and the console still
gets a human-readable line for live tailing.
"""
import datetime
import json
import os
import sys
import threading

from utils.parallel import worker_id

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "logs")
_lock = threading.Lock()


def _log_path() -> str:
    os.makedirs(_LOG_DIR, exist_ok=True)
    return os.path.join(_LOG_DIR, f"{worker_id()}.jsonl")


class TestLogger:
    """Usage:
        log = TestLogger(channel="sms", test_name="test_TC001", env="qa")
        log.info("Campaign created", campaign_id="SMS_CAMPAIGN_...")
        log.error("Import failed", correlation_id=msg_id, error=str(exc))
    """

    def __init__(self, channel: str = "-", test_name: str = "-", env: str = "-"):
        self.channel = channel
        self.test_name = test_name
        self.env = env
        self.worker = worker_id()

    def _emit(self, level: str, message: str, **fields):
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": level,
            "environment": self.env,
            "channel": self.channel,
            "test_name": self.test_name,
            "worker_id": self.worker,
            "message": message,
            **fields,
        }
        line = json.dumps(record, default=str)
        with _lock:
            print(f"[{record['timestamp']}][{self.worker}][{self.channel}] {message}"
                  + (f" | {fields}" if fields else ""), file=sys.stderr)
            with open(_log_path(), "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def info(self, message: str, **fields):
        self._emit("INFO", message, **fields)

    def warn(self, message: str, **fields):
        self._emit("WARN", message, **fields)

    def error(self, message: str, **fields):
        self._emit("ERROR", message, **fields)

    def debug(self, message: str, **fields):
        self._emit("DEBUG", message, **fields)
