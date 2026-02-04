from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class EloConfig:
    default_elo: float
    home_adv: float
    base_draw: float
    draw_decay: float


@dataclass(frozen=True)
class AppConfig:
    odds_api_key: str
    sport_key: str
    regions: str
    markets: str
    odds_format: str
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    edge_threshold: float
    min_odds: float
    max_alerts_per_run: int
    dedupe_ttl_hours: int
    dedupe_db_path: str
    log_level: str
    timezone: str
    elo: EloConfig


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    return value


def _get_float(name: str, default: float) -> float:
    raw = _get_env(name, str(default))
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid float for {name}: {raw}") from exc


def _get_int(name: str, default: int) -> int:
    raw = _get_env(name, str(default))
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid int for {name}: {raw}") from exc


def load_config() -> AppConfig:
    odds_api_key = _get_env("ODDS_API_KEY")
    if not odds_api_key:
        raise ValueError("ODDS_API_KEY is required")

    telegram_bot_token = _get_env("TELEGRAM_BOT_TOKEN") or None
    telegram_chat_id = _get_env("TELEGRAM_CHAT_ID") or None

    return AppConfig(
        odds_api_key=odds_api_key,
        sport_key=_get_env("SPORT_KEY", "soccer_epl") or "soccer_epl",
        regions=_get_env("REGIONS", "eu") or "eu",
        markets=_get_env("MARKETS", "h2h") or "h2h",
        odds_format=_get_env("ODDS_FORMAT", "decimal") or "decimal",
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        edge_threshold=_get_float("EDGE_THRESHOLD", 0.03),
        min_odds=_get_float("MIN_ODDS", 1.50),
        max_alerts_per_run=_get_int("MAX_ALERTS_PER_RUN", 15),
        dedupe_ttl_hours=_get_int("DEDUPE_TTL_HOURS", 24),
        dedupe_db_path=_get_env("DEDUPE_DB_PATH", "./data/dedupe.sqlite")
        or "./data/dedupe.sqlite",
        log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
        timezone=_get_env("TIMEZONE", "UTC") or "UTC",
        elo=EloConfig(
            default_elo=_get_float("DEFAULT_ELO", 1500),
            home_adv=_get_float("HOME_ADV", 60),
            base_draw=_get_float("BASE_DRAW", 0.26),
            draw_decay=_get_float("DRAW_DECAY", 600),
        ),
    )
