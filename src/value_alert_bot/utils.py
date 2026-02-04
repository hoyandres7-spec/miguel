from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, Iterable


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    return asdict(obj)


def backoff_delays(
    retries: int,
    base: float = 0.5,
    factor: float = 2.0,
    max_delay: float = 10.0,
) -> Iterable[float]:
    delay = base
    for _ in range(retries):
        jitter = random.uniform(0, 0.1 * delay)
        yield min(max_delay, delay + jitter)
        delay *= factor


def retry_with_backoff(
    func: Callable[[], Any],
    retries: int = 3,
    logger: logging.Logger | None = None,
) -> Any:
    last_exc: Exception | None = None
    for attempt, delay in enumerate(backoff_delays(retries=retries), start=1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if logger:
                logger.warning("Attempt %s failed: %s", attempt, exc)
            time.sleep(delay)
    if last_exc:
        raise last_exc
    return func()
