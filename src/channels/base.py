# Responsible for: the NotificationChannel interface all channels implement.
# Defines .send(notification) -> DeliveryResult (success/failure + optional
# error detail). Channels know nothing about retries, throttling, or
# scheduling — that logic lives entirely in delivery/.