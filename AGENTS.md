# AGENTS.md — news_notificator

This file tells any AI coding agent (or new contributor) how to set up the
environment, how the project is laid out, and what each file is responsible
for. Read this before touching code.

## 1. What this module is

This is the **final layer** of a larger pipeline. Two upstream layers already:
collect raw news from the internet, normalize titles, cluster, and dedupe —
all stored in PostgreSQL as processed data.

**This module only:**
1. Reads already-processed notification-ready rows from Postgres (read-only).
2. Decides which ones are allowed to send right now (throttle: max 50/day).
3. Delivers them to a phone via ntfy (and later, other channels).
4. Tracks delivery state so nothing is duplicated or silently lost.
5. Runs once per invocation and exits — it does **not** schedule itself.
   Scheduling (cron / systemd timer / k8s CronJob) is external, outside this
   codebase.

If you are an agent modifying this repo: do not add an internal scheduler
or long-running loop. Do not let this module write to upstream tables
(`articles`, clustering tables) — it only reads from the processed
notifications table and writes to its own `notification_deliveries` table.

## 2. Environment setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (reachable via `DATABASE_URL`)
- A running ntfy server/topic (self-hosted or ntfy.sh)

### Steps

```bash
# 1. Clone and enter the project
cd news_notificator

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt  # psycopg[binary], pydantic-settings, tenacity, httpx, pytest

# 4. Copy env template and fill in real values
cp .env.example .env
# Edit .env: DATABASE_URL, NTFY_SERVER, NTFY_TOPIC, MAX_NOTIFICATIONS_PER_DAY, etc.

# 5. Apply the DB schema (creates notification_deliveries table)
psql "$DATABASE_URL" -f config/schema.sql
# or, if using alembic:
# alembic upgrade head

# 6. Run the unit tests (no DB/network required)
pytest tests/unit

# 7. Run integration tests (requires a real/test Postgres + mock ntfy endpoint)
pytest tests/integration

# 8. Run one delivery cycle manually
python -m src.news_noficicator.main
```

### Docker (job-style, one-shot container)

```bash
docker build -t news-notificator .
docker run --rm --env-file .env news-notificator
```

Trigger this on a schedule externally (cron on the host, k8s CronJob, etc.).
The container is expected to start, run one dispatch cycle, and exit with a
status code (`0` = success, non-zero = failure) — external tooling should
alert on non-zero exits.

## 3. Project structure & file responsibilities

```
news_notificator/
├── AGENTS.md                     # this file
├── Dockerfile                    # builds the one-shot job image
├── requirements.txt              # pinned Python dependencies
├── .env.example                  # template for required env vars
├── .env                          # local secrets, gitignored
│
├── config/
│   ├── settings.py               # typed, validated config loaded from env (fail-fast on missing vars)
│   └── schema.sql                # DDL for notification_deliveries (and any local-only tables)
│
├── src/
│   ├── models/
│   │   ├── article.py            # raw ingested article shape (upstream-owned, read-only if touched at all)
│   │   ├── notification.py       # frozen, immutable content model: what to say in a notification
│   │   └── delivery.py           # mutable delivery-state model: status/attempts/timestamps per notification
│   │
│   ├── repositories/
│   │   ├── notification_repo.py  # READ-ONLY queries against the processed notifications table
│   │   └── delivery_repo.py      # owns all reads/writes to notification_deliveries (delivery state + audit)
│   │
│   ├── channels/
│   │   ├── base.py               # NotificationChannel interface: .send(notification) -> DeliveryResult
│   │   ├── ntfy.py               # ntfy-specific implementation: builds payload, POSTs, returns result
│   │   └── telegram.py           # telegram-specific implementation, same interface (stub until needed)
│   │
│   ├── delivery/
│   │   ├── throttle.py           # enforces the daily send cap and priority ordering when over quota
│   │   ├── retry.py              # backoff + circuit breaker wrapper around any channel.send() call
│   │   └── dispatcher.py         # single-run orchestration: fetch pending -> throttle -> send -> record state
│   │
│   └── news_noficicator/
│       └── main.py               # entrypoint: load config, wire dependencies, run one dispatch cycle, exit
│
└── tests/
    ├── unit/
    │   ├── test_throttle.py      # pure logic: quota enforcement, priority sorting — no DB/network
    │   ├── test_retry.py         # backoff/circuit-breaker behavior with a fake failing channel
    │   └── test_delivery_model.py
    └── integration/
        ├── test_delivery_repo.py # against a real/test Postgres instance
        └── test_ntfy_channel.py  # against a mock ntfy HTTP endpoint
```

## 4. Conventions for agents working in this repo

- **Never make `delivery_repo.py` and `notification_repo.py` share write access.**
  `notification_repo.py` is read-only, always.
- **Never put throttle/retry/window logic inside `channels/*.py`.** Channels
  only know how to send one payload and report success/failure. All
  decision-making about *whether* and *when* to send lives in `delivery/`.
- **`dispatcher.py` must be idempotent.** It can be invoked multiple times
  in the same day (external scheduler may overlap or double-fire) and must
  not double-send. Correctness comes from `delivery_repo` state, not from
  assuming single invocation.
- **No internal scheduling.** If you're tempted to add a loop, sleep(),
  or an in-process cron, stop — that belongs outside this module.
- **Keep `Notification` frozen.** Delivery lifecycle state goes in
  `Delivery`, referencing a notification by id — never mutate or subclass
  `Notification` to carry delivery status.