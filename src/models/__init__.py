from .article import Article
from .delivery import Delivery
from .notification import Notification

"""
Notification Dispatch Package

This package manages the data structures for an automated notification pipeline:
- Article: Ingested source content fetched from databases or feeds

- Notification: Processed, enriched messages ready for push distribution

- Delivery: Tracks transmission status, attempt counts, and delivery errors across channels
"""

__all__ = [
    "Article",
    "Delivery",
    "Notification",
]