import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

from src.config.settings import WORKER_METRICS
from src.models.db import cache
from src.services.scheduler import dispatch_one


log = logging.getLogger('scheduler')
stop = Event()
beat = Path(os.getenv('WORKER_BEAT', '/runtime/worker.beat'))


def main():
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    beat.parent.mkdir(parents=True, exist_ok=True)
    beat.unlink(missing_ok=True)
    processed = 0
    while not stop.is_set():
        try:
            for _ in range(64):
                if stop.is_set() or not dispatch_one():
                    break
                processed += 1
            stamp = datetime.now(timezone.utc).isoformat()
            cache.set(WORKER_METRICS, json.dumps({'checked_at': stamp, 'processed_since_start': processed}), ex=15)
            beat.touch()
        except Exception:
            log.exception('Scheduler sweep failed, retrying')
        stop.wait(1)
    beat.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
