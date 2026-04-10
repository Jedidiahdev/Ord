import asyncio
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Optional


logger = logging.getLogger("ord.resilience")


@dataclass
class RecoveryEvent:
    component: str
    operation: str
    retries_used: int
    healed: bool
    detail: str


class SelfHealingRuntime:
    """Minimal retry + fallback runtime for resilient agent operations."""

    def __init__(self, max_retries: int = 2, backoff_seconds: float = 0.1) -> None:
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.events: list[RecoveryEvent] = []

    def record(self, event: RecoveryEvent) -> None:
        self.events.append(event)
        level = logging.INFO if event.healed else logging.ERROR
        logger.log(level, "self-healing event | %s", event)

    def snapshot(self) -> Dict[str, Any]:
        healed = sum(1 for e in self.events if e.healed)
        return {
            "events": len(self.events),
            "healed": healed,
            "failed": len(self.events) - healed,
        }


def resilient_operation(runtime: Optional[SelfHealingRuntime] = None, component: str = "unknown"):
    runtime = runtime or SelfHealingRuntime()

    def decorator(func: Callable):
        is_coro = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(runtime.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    if attempt >= runtime.max_retries:
                        runtime.record(RecoveryEvent(component, func.__name__, attempt, False, str(exc)))
                        raise
                    await asyncio.sleep(runtime.backoff_seconds * (attempt + 1))
            raise RuntimeError("Unexpected retry flow")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(runtime.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt >= runtime.max_retries:
                        runtime.record(RecoveryEvent(component, func.__name__, attempt, False, str(exc)))
                        raise
            raise RuntimeError("Unexpected retry flow")

        return async_wrapper if is_coro else sync_wrapper

    return decorator
