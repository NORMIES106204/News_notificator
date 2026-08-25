# Responsible for: the immutable content of a single notification
# (title, description, impact, link, published_at, source).
# Frozen by design — this model represents "what to say," never
# "delivery status." Delivery lifecycle belongs in delivery.py instead.

from dataclasses import dataclass
from datetime import datetime


@dataclass (slots=True, frozen=True)
class Notification:
    """
    Structured information used to generate a user notification
    from a news article/event.
    """
    id: str
    """The unique identifier of the notification."""

    title: str
    """The title of the notification."""

    description: str
    """The description of the notification."""

    impact: str
    """The impact of the news article/event."""

    link: str
    """The link to the news article/event."""

    published_at: datetime
    """The timestamp of the news article/event."""

    source: str | None = None
    """The source of the news article/event."""

    cluster_article_count: int | None = None
    """The number of articles in the cluster, if applicable."""
