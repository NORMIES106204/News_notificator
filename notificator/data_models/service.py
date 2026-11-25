"""
Data structures for tracking the delivery state of published messages.

Standalone module: it does not import anything from news_models.py.
`reference_id` is a plain string the caller can set to whatever it wants
(an article id, a job id, ...), so the two modules stay decoupled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PublishStatus(str, Enum):
    PENDING = "pending"          # created, waiting to be sent
    SENDING = "sending"          # attempt in progress
    SENT = "sent"                # delivered successfully 
    THROTTLED = "throttled"      # rejected by rate limit, will retry later
    FAILED = "failed"            # last attempt failed, may be retried
    DEAD = "dead"                # retries exhausted, gave up 
    CANCELLED = "cancelled"      # cancelled before sending 
    TIMEOUT = "timeout"          # last attempt


FINAL_STATUSES = frozenset(
    {PublishStatus.SENT, PublishStatus.DEAD, PublishStatus.CANCELLED, PublishStatus.TIMEOUT}
)


@dataclass(slots=True)
class ThrottleInfo:
    """Rate-limit state reported by the destination or by our own limiter."""
    is_throttled: bool = False
    limit: int | None = None                  # max messages per window
    remaining: int | None = None              # messages left in current window
    window_seconds: float | None = None       # window size
    reset_at: datetime | None = None          # when the window resets
    retry_after_seconds: float | None = None  # delay requested by destination
    throttled_until: datetime | None = None   # earliest time we may send again


@dataclass(slots=True)
class PublishAttempt:
    """One try at sending a message (history entry)."""
    attempt_no: int
    started_at: datetime
    finished_at: datetime | None = None
    status: PublishStatus = PublishStatus.SENDING
    response_code: int | None = None          # e.g. HTTP status
    error: str | None = None
    throttle: ThrottleInfo | None = None
    duration_ms: float | None = None


@dataclass(slots=True)
class PublishMessage:
    """A message to publish, with its full delivery state."""
    id: str
    destination: str                          # channel / topic / endpoint name
    payload: str                              # rendered message body
    reference_id: str | None = None           # optional free-form external id

    status: PublishStatus = PublishStatus.PENDING

    # timing
    created_at: datetime | None = None
    scheduled_at: datetime | None = None      # when it should be sent
    sent_at: datetime | None = None           # when it was delivered
    last_attempt_at: datetime | None = None
    next_attempt_at: datetime | None = None   # retry / throttle wake-up time

    # retry
    attempt_count: int = 0
    max_attempts: int = 5

    # result
    remote_message_id: str | None = None      # id returned by the destination
    last_error: str | None = None

    # throttle + history
    throttle: ThrottleInfo = field(default_factory=ThrottleInfo)
    attempts: list[PublishAttempt] = field(default_factory=list)

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES

    @property
    def can_retry(self) -> bool:
        return not self.is_final and self.attempt_count < self.max_attempts