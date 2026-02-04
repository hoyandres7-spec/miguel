from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import List

from value_alert_bot.config import AppConfig, load_config
from value_alert_bot.dedupe import DedupeStore, build_hash
from value_alert_bot.models.elo_soccer_1x2 import EloSoccer1X2
from value_alert_bot.notifier.console import ConsoleNotifier
from value_alert_bot.notifier.telegram import TelegramNotifier
from value_alert_bot.odds_api import fetch_odds
from value_alert_bot.scoring import EventOdds, Signal, build_signals, sort_and_limit
from value_alert_bot.utils import setup_logging

logger = logging.getLogger(__name__)


def _format_commence_time(commence_time: str, timezone: str) -> str:
    if timezone.upper() == "UTC":
        return commence_time
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        return commence_time

    try:
        if commence_time.endswith("Z"):
            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(commence_time)
        local_dt = dt.astimezone(ZoneInfo(timezone))
        return local_dt.isoformat()
    except Exception:
        return commence_time


def _build_signal_hash(signal: Signal, model_version: str) -> str:
    odds_key = f"{signal.odds:.2f}"
    return build_hash(
        signal.event_id,
        signal.market,
        signal.selection,
        signal.bookmaker,
        odds_key,
        model_version,
    )


def _collect_signals(
    events: List[EventOdds],
    config: AppConfig,
) -> List[Signal]:
    model = EloSoccer1X2(config.elo)
    all_signals: List[Signal] = []
    for event in events:
        model_probs = model.probability_1x2(event.home_team, event.away_team)
        signals = build_signals(
            event,
            model_probs,
            edge_threshold=config.edge_threshold,
            min_odds=config.min_odds,
        )
        for signal in signals:
            formatted_time = _format_commence_time(signal.commence_time, config.timezone)
            all_signals.append(
                Signal(
                    event_id=signal.event_id,
                    home_team=signal.home_team,
                    away_team=signal.away_team,
                    commence_time=formatted_time,
                    market=signal.market,
                    selection=signal.selection,
                    odds=signal.odds,
                    bookmaker=signal.bookmaker,
                    p_model=signal.p_model,
                    p_implied=signal.p_implied,
                    edge=signal.edge,
                )
            )
    return sort_and_limit(all_signals, config.max_alerts_per_run)


def _send_signals(
    signals: List[Signal],
    config: AppConfig,
    dry_run: bool,
) -> None:
    notifier = ConsoleNotifier()
    telegram = None
    if config.telegram_bot_token and config.telegram_chat_id:
        telegram = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)

    for signal in signals:
        notifier.send(signal)
        if dry_run:
            continue
        if telegram:
            telegram.send(signal)


def run_command(args: argparse.Namespace) -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Fetching odds for sport=%s regions=%s markets=%s", config.sport_key, config.regions, config.markets)
    odds_response = fetch_odds(
        api_key=config.odds_api_key,
        sport_key=config.sport_key,
        regions=config.regions,
        markets=config.markets,
        odds_format=config.odds_format,
        fixture_path=args.fixture,
    )

    dedupe = DedupeStore(config.dedupe_db_path, config.dedupe_ttl_hours)
    dedupe.purge()

    signals = _collect_signals(odds_response.events, config)
    model_version = EloSoccer1X2(config.elo).model_version
    filtered_signals: List[Signal] = []
    for signal in signals:
        hash_value = _build_signal_hash(signal, model_version)
        if dedupe.seen(hash_value):
            continue
        filtered_signals.append(signal)
        dedupe.add(hash_value)

    if not filtered_signals:
        logger.info("No alerts after dedupe/threshold filters")
        return

    _send_signals(filtered_signals, config, dry_run=args.dry_run)


def export_command(args: argparse.Namespace) -> None:
    config = load_config()
    setup_logging(config.log_level)

    odds_response = fetch_odds(
        api_key=config.odds_api_key,
        sport_key=config.sport_key,
        regions=config.regions,
        markets=config.markets,
        odds_format=config.odds_format,
        fixture_path=args.fixture,
    )
    signals = _collect_signals(odds_response.events, config)
    payload = [asdict(signal) for signal in signals]
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    logger.info("Exported %s signals to %s", len(payload), args.out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Value alert bot")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run the bot once")
    run_parser.add_argument("--dry-run", action="store_true", help="Only print alerts")
    run_parser.add_argument("--fixture", help="Path to odds JSON fixture", default=None)
    run_parser.set_defaults(func=run_command)

    export_parser = sub.add_parser("export", help="Export signals to JSON")
    export_parser.add_argument("--out", required=True, help="Output JSON file")
    export_parser.add_argument("--fixture", help="Path to odds JSON fixture", default=None)
    export_parser.set_defaults(func=export_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
