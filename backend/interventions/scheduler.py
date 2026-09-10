"""
AAROH — SLA Overdue Scanner & Background Lifecycle Scheduler
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Provides automated, recurring lifecycle scanning for SLA breaches on active interventions:
- Dispatches INTERVENTION_OVERDUE notifications to assigned officers and district supervisors.
- Logs SLA_BREACHED audit events to CaseEvent.
- Can run as an in-process background daemon, a standalone CLI process, or via cron / webhook.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.interventions.db_service import db_operational_service

logger = logging.getLogger("aaroh.scheduler")


class PeriodicOverdueScanner:
    """
    Background worker that periodically triggers SLA overdue evaluations.
    Thread-safe, daemonized, and resilient against database connection drops.
    """

    def __init__(self, default_interval_seconds: int = 300) -> None:
        self.default_interval = default_interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_scan_time: Optional[float] = None
        self._last_scan_count: int = 0

    def scan_once(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Executes a single scan cycle immediately.
        Can be invoked directly from API endpoints, CLI, or test suites.
        """
        logger.info("Executing SLA overdue scan cycle...")
        overdue = db_operational_service.check_and_notify_overdue_interventions(db=db, auto_commit=True)
        self._last_scan_time = time.time()
        self._last_scan_count = len(overdue)
        logger.info("SLA overdue scan complete. Identified %d overdue interventions.", len(overdue))
        return overdue

    def _run_loop(self, interval_seconds: int) -> None:
        logger.info("PeriodicOverdueScanner started with interval=%ds.", interval_seconds)
        while not self._stop_event.is_set():
            try:
                self.scan_once()
            except Exception as e:
                logger.error("Error during periodic SLA overdue scan: %s", e, exc_info=True)
            # Sleep in short increments to respond quickly to stop requests
            for _ in range(int(interval_seconds * 2)):
                if self._stop_event.is_set():
                    break
                time.sleep(0.5)
        logger.info("PeriodicOverdueScanner stopped.")

    def start(self, interval_seconds: Optional[int] = None) -> None:
        """Starts the periodic scanner background thread if not already running."""
        if self.is_running():
            logger.warning("PeriodicOverdueScanner is already running.")
            return

        interval = interval_seconds or self.default_interval
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(interval,),
            daemon=True,
            name="SLAOverdueScannerThread",
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Signals the scanner thread to stop and waits for termination."""
        if not self.is_running():
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "running": self.is_running(),
            "default_interval_seconds": self.default_interval,
            "last_scan_time": self._last_scan_time,
            "last_scan_count": self._last_scan_count,
        }


# Global singleton instance
overdue_scanner = PeriodicOverdueScanner()
