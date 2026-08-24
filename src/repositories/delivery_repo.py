# Responsible for: full ownership of the notification_deliveries table.
# All reads and writes to delivery state live here: creating a pending
# delivery record, marking in_flight/delivered/failed/dead_letter,
# incrementing attempts, and querying "what's pending right now" or
# "what failed and needs retry." This is the single source of truth that
# makes duplicate-send prevention and dead-letter tracking possible.