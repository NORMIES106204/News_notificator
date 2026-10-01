from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Delivery:
    notification_id: str
    channel: str
    status: str
    attempts: int
    created_at: datetime
    updated_at: datetime | None = None
    error: str | None = None