"""
Typed, validated application configuration.

This module owns the boundary between "stuff that comes from the
environment" and "stuff the rest of the codebase can trust". Nothing else in
this project should call `os.environ` directly — if a module needs
environment-specific config, it goes through `settings` (or `load_settings`
in tests), never a hardcoded value or an ad-hoc `os.environ.get`.

Loading strategy: reads from `os.environ` by default. `load_settings()` also
accepts an explicit mapping, purely so tests can construct a `Settings`
without mutating real process environment variables. This module does NOT
load `.env` files itself (that would mix "where config comes from" with
"how config is validated") — if `.env` loading is wanted for local dev, it
belongs in the entrypoint (main.py) or Docker layer, before this module is
imported.

Fail-fast: `load_settings()` validates everything up front and raises a
single `ConfigError` listing every problem found (missing vars, wrong
types, out-of-range values) rather than failing on the first one — so a
misconfigured deployment tells you everything wrong in one shot instead of
one error per restart.
"""

import os
from dataclasses import dataclass
from typing import Mapping, Optional

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(Exception):
    """
    Raised when required configuration is missing or invalid.

    Carries every problem found in a single message (not just the first),
    so a misconfigured environment can be fixed in one pass instead of
    discovered one restart at a time.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        joined = "; ".join(problems)
        super().__init__(f"Invalid configuration: {joined}")


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Validated application configuration.

    Attributes:
        database_url: Postgres connection string for notification_repo.py /
            delivery_repo.py (read-only vs read-write is enforced by those
            modules, not by having two separate URLs here).
        ntfy_server: Base URL of the ntfy server/instance to publish to.
        ntfy_topic: ntfy topic this deployment publishes notifications to.
        max_notifications_per_day: Hard cap enforced by throttle.py. Must be
            a positive integer.
        log_level: Root log level for the process (e.g. delivery failures
            and dead-letter promotions are surfaced here, not via a
            separate notification-of-failure mechanism).
    """

    database_url: str
    ntfy_server: str
    ntfy_topic: str
    max_notifications_per_day: int
    log_level: str = "INFO"
    connection_status : str


def _require_str(env: Mapping[str, str], key: str, problems: list[str]) -> str:
    value = env.get(key, "").strip()
    if not value:
        problems.append(f"{key} is required but was not set")
    return value


def _parse_positive_int(env: Mapping[str, str], key: str, problems: list[str]) -> int:
    raw = env.get(key, "").strip()
    if not raw:
        problems.append(f"{key} is required but was not set")
        return 0
    try:
        value = int(raw)
    except ValueError:
        problems.append(f"{key} must be an integer, got {raw!r}")
        return 0
    if value <= 0:
        problems.append(f"{key} must be a positive integer, got {value}")
        return 0
    return value


def _parse_log_level(env: Mapping[str, str], key: str, problems: list[str]) -> str:
    raw = env.get(key, "").strip().upper()
    if not raw:
        return "INFO"
    if raw not in _VALID_LOG_LEVELS:
        problems.append(
            f"{key} must be one of {sorted(_VALID_LOG_LEVELS)}, got {raw!r}"
        )
        return "INFO"
    return raw


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """
    Build a validated Settings instance from environment variables.

    Args:
        env: Mapping to read from. Defaults to `os.environ`. Tests should
            pass an explicit dict here rather than mutating real env vars.

    Raises:
        ConfigError: if any required variable is missing or any value is
            invalid. The exception message lists every problem found, not
            just the first.
    """
    source = env if env is not None else os.environ
    problems: list[str] = []

    database_url = _require_str(source, "DATABASE_URL", problems)
    ntfy_server = _require_str(source, "NTFY_SERVER", problems)
    ntfy_topic = _require_str(source, "NTFY_TOPIC", problems)
    max_notifications_per_day = _parse_positive_int(
        source, "MAX_NOTIFICATIONS_PER_DAY", problems
    )
    log_level = _parse_log_level(source, "LOG_LEVEL", problems)

    if problems:
        raise ConfigError(problems)

    return Settings(
        database_url=database_url,
        ntfy_server=ntfy_server,
        ntfy_topic=ntfy_topic,
        max_notifications_per_day=max_notifications_per_day,
        log_level=log_level,
    )


_cached_settings: Optional[Settings] = None


def get_settings(force_reload: bool = False) -> Settings:
    """
    Return the process-wide Settings singleton, loading it from
    `os.environ` on first access and caching it thereafter.

    This is deliberately lazy rather than evaluated at import time: importing
    this module (e.g. just to reference `ConfigError`) must not require a
    fully configured environment. Validation only happens when configuration
    is actually needed.
    """
    global _cached_settings
    if _cached_settings is None or force_reload:
        _cached_settings = load_settings()
    return _cached_settings


class _LazySettingsProxy:
    """
    Forwards attribute access to the cached Settings singleton, loading it
    on first use. Lets the rest of the codebase do
    `from config.settings import settings; settings.database_url` as a
    single global instance, without paying the fail-fast validation cost
    (or requiring a configured environment) at import time.
    """

    def __getattr__(self, name: str):
        return getattr(get_settings(), name)


settings = _LazySettingsProxy()