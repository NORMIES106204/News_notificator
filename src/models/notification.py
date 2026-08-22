from dataclasses import dataclass
from datetime import datetime


@dataclass (slots=True, frozen=True)
class Notification:
    """
    Structured information used to generate a user notification
    from a news article/event.
    """

    title: str
    """The title of the notification."""

    description: str
    """The description of the notification."""

    impact: str
    """The impact of the new"""

    link: str
    """The link to the news article/event."""

    pulished_at: datetime
    """The timestamp of the news article/event."""

    source: str | None = None
    """The source of the news article/event."""

