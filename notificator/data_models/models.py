"""Data structures mirroring the News Intelligence database schema."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FeedType(str, Enum):
    RSS = "rss"
    ATOM = "atom"
    API = "api"


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    name: str
    website: str
    country: str | None = None
    language: str | None = None
    categories: tuple[str, ...] = ()
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class Feed:
    id: str
    source_id: str
    name: str
    url: str
    type: FeedType
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    source_id: str
    feed_id: str
    title: str
    url: str
    collected_at: datetime
    description: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    processed: bool = False