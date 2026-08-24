# Responsible for: mirroring the raw Article shape produced upstream.
# Read-only reference model — this layer does not create, mutate, or
# persist Article rows. Only present here if a query genuinely needs to
# join against article data; otherwise this layer should not import it.