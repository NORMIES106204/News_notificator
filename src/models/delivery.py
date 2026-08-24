# Responsible for: the mutable delivery lifecycle for a notification.
# Tracks id, notification_id (FK reference), status (pending/in_flight/
# delivered/failed/dead_letter), attempts, next_retry_at, sent_at.
# Kept separate from Notification so content stays frozen/immutable while
# delivery state can change freely as attempts are made.