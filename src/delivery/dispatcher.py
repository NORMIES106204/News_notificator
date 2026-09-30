# Responsible for: the single-run orchestration of one delivery cycle.
# Sequence: pull pending notifications (notification_repo + delivery_repo)
# -> filter/order via throttle.py -> send each via a channel, wrapped by
# retry.py -> record the outcome in delivery_repo. Must be idempotent and
# safe to invoke repeatedly without double-sending; does not loop or sleep
# internally — one call in, one exit code out.