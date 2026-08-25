"""
Mutable delivery-state model for a single notification's delivery lifecycle.

A Delivery tracks *whether and how* a Notification was sent — it never
carries content (that lives on the frozen `Notification`, referenced here
only by `notification_id`). `delivery_repo.py` is the single owner of reads
and writes to the persisted form of this model; nothing else writes
delivery state.

State machine:

    pending --> in_flight --> delivered              (terminal, success)
                    ^  |
                    |  +--> failed --> dead_letter    (terminal, exhausted)
                    |          |
                    +----------+   (retry: failed --> in_flight)

- `dead_letter` is a distinct terminal state from `failed`. `failed` is
  transient/retryable; `dead_letter` means the retry budget
  (RETRY_MAX_ATTEMPTS) is exhausted. Promoting `failed --> dead_letter` is a
  decision made by `retry.py` (it owns the attempts-vs-max comparison); this
  model only enforces that the transition itself is legal and reachable.
- `dead_letter` is permanent. There is no automatic re-promotion out of it.
  A channel coming back online is handled by the channel-level circuit
  breaker in `retry.py`, which is orthogonal to any single notification's
  state. Requeuing a dead-lettered item is an explicit manual/operator
  action (not implemented here), never something the dispatcher does on its
  own.
- Failures are surfaced via logging (in retry.py / dispatcher.py) — this
  model does not send alerts or notifications about its own failures.

No business validation happens here beyond legal state transitions — e.g.
this model does not enforce `RETRY_MAX_ATTEMPTS`, since that threshold is
config-driven and belongs to retry.py.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DeliveryStatus(str, Enum):
    """All legal states for a Delivery's lifecycle."""

    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class InvalidDeliveryTransition(Exception):
    """
    Raised when code attempts to move a Delivery to a status that is not
    reachable from its current status.

    Carries the offending (current, attempted) pair in the message so
    callers get actionable context rather than a bare failure — this is a
    "no silent failure" boundary, never caught-and-ignored internally.
    """

    def __init__(self, current: DeliveryStatus, attempted: DeliveryStatus) -> None:
        self.current = current
        self.attempted = attempted
        super().__init__(
            f"Cannot transition Delivery from '{current.value}' to "
            f"'{attempted.value}'."
        )


# Legal transitions: current status -> set of statuses it may move to.
# Terminal states (delivered, dead_letter) map to an empty set.
_ALLOWED_TRANSITIONS: dict[DeliveryStatus, frozenset[DeliveryStatus]] = {
    DeliveryStatus.PENDING: frozenset({DeliveryStatus.IN_FLIGHT}),
    DeliveryStatus.IN_FLIGHT: frozenset(
        {DeliveryStatus.DELIVERED, DeliveryStatus.FAILED}
    ),
    DeliveryStatus.FAILED: frozenset(
        {DeliveryStatus.IN_FLIGHT, DeliveryStatus.DEAD_LETTER}
    ),
    DeliveryStatus.DELIVERED: frozenset(),
    DeliveryStatus.DEAD_LETTER: frozenset(),
}


@dataclass(slots=True)
class Delivery:
    """
    Mutable delivery-state record for one Notification's send lifecycle.

    Attributes:
        id: Delivery record identifier (primary key in notification_deliveries).
        notification_id: Foreign reference to the immutable Notification this
            delivery is for. This is the only link between the two models.
        status: Current point in the state machine described above.
        attempts: Number of send attempts made so far. Incremented each time
            the delivery moves into `in_flight`.
        next_retry_at: When retry.py should next attempt delivery, set when
            moving into `failed`. None once delivered or dead-lettered.
        sent_at: Timestamp of successful delivery. None until `delivered`.
        created_at: When this delivery record was first created.
        updated_at: When this delivery record was last mutated. Callers are
            expected to refresh this via `touch()` (or their own timestamp)
            when persisting a change; this model does not read a clock
            itself, to keep it deterministic and easy to test.

    All state changes go through the `mark_*` methods below rather than
    direct attribute assignment, so that illegal transitions raise
    `InvalidDeliveryTransition` instead of silently producing a corrupt
    state.
    """

    id: str
    notification_id: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    next_retry_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def _transition(self, new_status: DeliveryStatus) -> None:
        """Validate and apply a status change, or raise if illegal."""
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if new_status not in allowed:
            raise InvalidDeliveryTransition(self.status, new_status)
        self.status = new_status

    def mark_in_flight(self, now: datetime) -> None:
        """
        Move this delivery into `in_flight` and count the attempt.

        Legal from `pending` or `failed` (i.e. first attempt or a retry).
        `now` is passed in explicitly (rather than read from the system
        clock) so callers control time and this stays trivially testable.
        """
        self._transition(DeliveryStatus.IN_FLIGHT)
        self.attempts += 1
        self.updated_at = now

    def mark_delivered(self, now: datetime) -> None:
        """Move this delivery into the terminal `delivered` state."""
        self._transition(DeliveryStatus.DELIVERED)
        self.sent_at = now
        self.next_retry_at = None
        self.updated_at = now

    def mark_failed(self, now: datetime, next_retry_at: Optional[datetime]) -> None:
        """
        Move this delivery into `failed` (transient, retryable).

        `next_retry_at` is supplied by retry.py's backoff calculation. It
        may be None if the caller intends to immediately promote this to
        `dead_letter` instead (see mark_dead_letter).
        """
        self._transition(DeliveryStatus.FAILED)
        self.next_retry_at = next_retry_at
        self.updated_at = now

    def mark_dead_letter(self, now: datetime) -> None:
        """
        Move this delivery into the terminal `dead_letter` state.

        Called by retry.py once `attempts >= RETRY_MAX_ATTEMPTS`. This is
        permanent — there is no method on this model to leave dead_letter.
        """
        self._transition(DeliveryStatus.DEAD_LETTER)
        self.next_retry_at = None
        self.updated_at = now