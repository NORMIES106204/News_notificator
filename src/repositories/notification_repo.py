#here lies the notification repository which main purpose is to store the notifications in a list and provide methods to add, remove, and retrieve new from PostgreSQL
#data stored here will be structured as a list of Notification objects, which will be defined in the models/notification.py file

from datetime import datetime
from typing import List

import psycopg

from src.models.notification import Notification

class NotificationRepository:

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.notifications: List[Notification] = []

    def add_notification(self, notification: Notification) -> None:
        """Add a new notification to the repository."""
        self.notifications.append(notification)

    def remove_notification(self, notification: Notification) -> None:
        """Remove a notification from the repository."""
        self.notifications.remove(notification)

    def get_notifications(self) -> List[Notification]:
        """Retrieve all notifications from the repository."""
        return self.notifications

    def fetch_notifications_from_db(self) -> None:
        """Fetch notifications from the PostgreSQL database and store them in the repository."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title, description, impact, link, published_at, source FROM notifications")
                rows = cur.fetchall()
                for row in rows:
                    notification = Notification(
                        title=row[0],
                        description=row[1],
                        impact=row[2],
                        link=row[3],
                        published_at=row[4],
                        source=row[5]
                    )
                    
                    self.add_notification(notification)