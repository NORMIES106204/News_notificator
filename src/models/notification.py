from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Notification:
    title: str
    description: str
    impact_on_world: str
    link: str
    published_at: datetime
    event_at: datetime | None = None