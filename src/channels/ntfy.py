# Responsible for: sending a single Notification via ntfy.
# Builds the ntfy-specific payload (impact -> priority header, link ->
# click action, source -> tag), POSTs it, and returns a DeliveryResult.
# Contains no retry, throttle, or scheduling logic — a bare, single-attempt
# implementation of the NotificationChannel interface.