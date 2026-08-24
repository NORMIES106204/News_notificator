# Responsible for: typed, validated application configuration.
# Loads and validates all required env vars (DATABASE_URL, NTFY_SERVER,
# NTFY_TOPIC, MAX_NOTIFICATIONS_PER_DAY, retry limits, etc.) at startup.
# Fails fast with a clear error if anything required is missing — no module
# outside this file should call os.getenv() directly.