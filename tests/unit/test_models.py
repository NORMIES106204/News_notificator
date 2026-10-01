from datetime import datetime, timezone

import pytest

from src.models import Article, Delivery, Notification


def test_article_can_be_created():
    published_at = datetime(
        2026,
        10,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    collected_at = datetime(
        2026,
        10,
        1,
        10,
        5,
        tzinfo=timezone.utc,
    )

    article = Article(
        id="article-001",
        source_id="source-001",
        feed_id="feed-001",
        title="Example article",
        description="Example description",
        url="https://example.com/article",
        published_at=published_at,
        collected_at=collected_at,
        language="en",
        processed=False,
    )

    assert article.id == "article-001"
    assert article.source_id == "source-001"
    assert article.feed_id == "feed-001"
    assert article.title == "Example article"
    assert article.description == "Example description"
    assert article.url == "https://example.com/article"
    assert article.published_at == published_at
    assert article.collected_at == collected_at
    assert article.language == "en"
    assert article.processed is False


def test_article_allows_nullable_fields():
    collected_at = datetime.now(timezone.utc)

    article = Article(
        id="article-001",
        source_id="source-001",
        feed_id="feed-001",
        title="Example article",
        description=None,
        url="https://example.com/article",
        published_at=None,
        collected_at=collected_at,
        language=None,
        processed=False,
    )

    assert article.description is None
    assert article.published_at is None
    assert article.language is None


def test_article_is_immutable():
    article = Article(
        id="article-001",
        source_id="source-001",
        feed_id="feed-001",
        title="Example article",
        description=None,
        url="https://example.com/article",
        published_at=None,
        collected_at=datetime.now(timezone.utc),
        language=None,
        processed=False,
    )

    with pytest.raises(AttributeError):
        article.processed = True


def test_notification_can_be_created():
    published_at = datetime(
        2026,
        10,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    notification = Notification(
        title="Important news",
        description="Something happened.",
        impact_on_world="Potential economic impact.",
        link="https://example.com/article",
        published_at=published_at,
    )

    assert notification.title == "Important news"
    assert notification.description == "Something happened."
    assert notification.impact_on_world == "Potential economic impact."
    assert notification.link == "https://example.com/article"
    assert notification.published_at == published_at
    assert notification.event_at is None


def test_notification_can_have_event_time():
    published_at = datetime(
        2026,
        10,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    event_at = datetime(
        2026,
        10,
        2,
        12,
        0,
        tzinfo=timezone.utc,
    )

    notification = Notification(
        title="Upcoming event",
        description="An event is scheduled.",
        impact_on_world="Potential impact.",
        link="https://example.com/article",
        published_at=published_at,
        event_at=event_at,
    )

    assert notification.event_at == event_at


def test_delivery_can_be_created():
    created_at = datetime.now(timezone.utc)

    delivery = Delivery(
        notification_id="notification-001",
        channel="telegram",
        status="sent",
        attempts=1,
        created_at=created_at,
    )

    assert delivery.notification_id == "notification-001"
    assert delivery.channel == "telegram"
    assert delivery.status == "sent"
    assert delivery.attempts == 1
    assert delivery.created_at == created_at
    assert delivery.updated_at is None
    assert delivery.error is None


def test_delivery_can_store_failure_information():
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)

    delivery = Delivery(
        notification_id="notification-001",
        channel="telegram",
        status="failed",
        attempts=3,
        created_at=created_at,
        updated_at=updated_at,
        error="Telegram API unavailable",
    )

    assert delivery.status == "failed"
    assert delivery.attempts == 3
    assert delivery.updated_at == updated_at
    assert delivery.error == "Telegram API unavailable"


def test_delivery_is_immutable():
    delivery = Delivery(
        notification_id="notification-001",
        channel="telegram",
        status="sent",
        attempts=1,
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(AttributeError):
        delivery.status = "failed"