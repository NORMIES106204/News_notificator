# Responsible for: mirroring the raw Article shape produced upstream.
# Read-only reference model — this layer does not create, mutate, or
# persist Article rows. Only present here if a query genuinely needs to
# join against article data; otherwise this layer should not import it.

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