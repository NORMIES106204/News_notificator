# Responsible for: retry-with-backoff and circuit-breaker behavior around
# any channel.send() call. Wraps a channel call, retries transient
# failures with increasing delay up to a max attempt count, and short-
# circuits (stops calling) after repeated consecutive failures to avoid
# hammering a downed channel endpoint.