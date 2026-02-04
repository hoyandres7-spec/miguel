from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from value_alert_bot.scoring import EventOdds, SelectionOdds
from value_alert_bot.utils import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OddsApiResponse:
    events: List[EventOdds]


def _fetch_fixture(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_odds(
    api_key: str,
    sport_key: str,
    regions: str,
    markets: str,
    odds_format: str,
    timeout: float = 10.0,
    fixture_path: Optional[str] = None,
) -> OddsApiResponse:
    if fixture_path:
        logger.info("Using fixture payload: %s", fixture_path)
        payload = _fetch_fixture(fixture_path)
        return OddsApiResponse(events=parse_events(payload))

    fixture_env = os.getenv("ODDS_API_FIXTURE_PATH")
    if fixture_env:
        logger.info("Using fixture payload from ODDS_API_FIXTURE_PATH")
        payload = _fetch_fixture(fixture_env)
        return OddsApiResponse(events=parse_events(payload))

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format,
    }

    def _request() -> List[dict]:
        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "requests is required to call The Odds API. Install dependencies first."
            ) from exc
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    payload = retry_with_backoff(_request, logger=logger)
    return OddsApiResponse(events=parse_events(payload))


def parse_events(payload: List[dict]) -> List[EventOdds]:
    events: List[EventOdds] = []
    for event in payload:
        event_id = str(event.get("id") or "")
        home_team = event.get("home_team") or ""
        away_team = event.get("away_team") or ""
        commence_time = event.get("commence_time") or ""
        best_home: Optional[SelectionOdds] = None
        best_draw: Optional[SelectionOdds] = None
        best_away: Optional[SelectionOdds] = None

        for bookmaker in event.get("bookmakers", []) or []:
            book_key = bookmaker.get("key") or bookmaker.get("title") or "book"
            for market in bookmaker.get("markets", []) or []:
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []) or []:
                    name = outcome.get("name") or ""
                    price = outcome.get("price")
                    if not price:
                        continue
                    if name == home_team:
                        best_home = _best_price(best_home, SelectionOdds("home", price, book_key))
                    elif name == away_team:
                        best_away = _best_price(best_away, SelectionOdds("away", price, book_key))
                    elif name.lower() == "draw":
                        best_draw = _best_price(best_draw, SelectionOdds("draw", price, book_key))

        if best_home and best_away:
            events.append(
                EventOdds(
                    event_id=event_id or f"{home_team}-{away_team}-{commence_time}",
                    home_team=home_team,
                    away_team=away_team,
                    commence_time=commence_time,
                    market="h2h",
                    odds_home=best_home,
                    odds_draw=best_draw,
                    odds_away=best_away,
                )
            )
        else:
            logger.warning(
                "Skipping event due to incomplete odds: %s vs %s", home_team, away_team
            )
    return events


def _best_price(existing: Optional[SelectionOdds], candidate: SelectionOdds) -> SelectionOdds:
    if existing is None or candidate.odds > existing.odds:
        return candidate
    return existing
