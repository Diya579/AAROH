"""
AAROH — Standalone SLA Overdue CLI Runner
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Usage:
  # Run once (e.g. for Linux cron / Cloud Scheduler / Kubernetes CronJob):
  python -m backend.interventions.check_overdue --once

  # Run continuously as a background daemon (e.g. Docker container sidecar):
  python -m backend.interventions.check_overdue --daemon --interval 300
"""

import argparse
import logging
import sys
import time

from backend.interventions.scheduler import overdue_scanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aaroh.check_overdue")


def main() -> None:
    parser = argparse.ArgumentParser(description="AAROH SLA Overdue Scanner CLI")
    parser.add_argument("--once", action="store_true", help="Run a single scan cycle and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in foreground loop")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds between scans (default: 300)")

    args = parser.parse_args()

    if args.once or not args.daemon:
        logger.info("Starting single SLA overdue scan cycle...")
        overdue = overdue_scanner.scan_once()
        print(f"Scan complete. Overdue interventions detected: {len(overdue)}")
        for item in overdue:
            print(f"  - Intervention #{item['intervention_id']} (Case: {item['case_id']}, District: {item['district']}, Due: {item['due_at']})")
        sys.exit(0)

    logger.info("Starting continuous SLA overdue scanner (interval=%ds)...", args.interval)
    try:
        while True:
            overdue_scanner.scan_once()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Scanner terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
