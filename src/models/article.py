from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    source_id: str
    feed_id: str
    title: str
    description: str | None
    url: str
    published_at: datetime | None
    collected_at: datetime
    language: str | None
    processed: bool