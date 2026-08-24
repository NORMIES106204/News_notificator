# Responsible for: enforcing the daily delivery cap (max 50/day) and
# deciding which pending notifications get sent when there are more
# candidates than remaining quota (priority/impact-based selection).
# Pure logic — no DB or network calls — so it can be unit tested with
# plain in-memory data. Must behave correctly no matter how often it's
# invoked per day (external scheduler may call this many times).