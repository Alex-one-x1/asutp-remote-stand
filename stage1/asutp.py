#!/usr/bin/env python3
"""Печатает метку времени и счётчик каждые N секунд — удобно для проверки,
что процесс/скрипт жив (heartbeat)."""

import time
import sys
from datetime import datetime

INTERVAL = 3  # секунд между печатями

def main():
    counter = 0
    try:
        while True:
            counter += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[heartbeat #{counter}] {now}", flush=True)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nОстановлено пользователем (Ctrl+C)", file=sys.stderr)


if __name__ == "__main__":
    main()
