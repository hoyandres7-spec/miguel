from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from value_alert_bot.models.base import ModelOutcome


@dataclass(frozen=True)
class SelectionOdds:
    selection: str
    odds: float
    bookmaker: str


@dataclass(frozen=True)
class EventOdds:
    event_id: str
    home_team: str
    away_team: str
    commence_time: str
    market: str
    odds_home: Optional[SelectionOdds]
    odds_draw: Optional[SelectionOdds]
    odds_away: Optional[SelectionOdds]


@dataclass(frozen=True)
class Signal:
    event_id: str
    home_team: str
    away_team: str
    commence_time: str
    market: str
    selection: str
    odds: float
    bookmaker: str
    p_model: float
    p_implied: float
    edge: float


def implied_probabilities(odds: Dict[str, float]) -> Dict[str, float]:
    inv = {key: 1.0 / value for key, value in odds.items() if value > 0}
    total = sum(inv.values())
    if total <= 0:
        raise ValueError("Invalid odds for implied probability")
    return {key: value / total for key, value in inv.items()}


def build_signals(
    event_odds: EventOdds,
    model_probs: ModelOutcome,
    edge_threshold: float,
    min_odds: float,
) -> List[Signal]:
    odds_map: Dict[str, SelectionOdds] = {
        "home": event_odds.odds_home,
        "draw": event_odds.odds_draw,
        "away": event_odds.odds_away,
    }
    odds_clean = {key: val.odds for key, val in odds_map.items() if val is not None}
    implied = implied_probabilities(odds_clean)
    signals: List[Signal] = []

    model_map = {
        "home": model_probs.home_win,
        "draw": model_probs.draw,
        "away": model_probs.away_win,
    }

    for selection_key, selection_odds in odds_map.items():
        if selection_odds is None:
            continue
        p_model = model_map[selection_key]
        p_implied = implied[selection_key]
        edge = p_model - p_implied
        if edge >= edge_threshold and selection_odds.odds >= min_odds:
            signals.append(
                Signal(
                    event_id=event_odds.event_id,
                    home_team=event_odds.home_team,
                    away_team=event_odds.away_team,
                    commence_time=event_odds.commence_time,
                    market=event_odds.market,
                    selection=selection_key,
                    odds=selection_odds.odds,
                    bookmaker=selection_odds.bookmaker,
                    p_model=p_model,
                    p_implied=p_implied,
                    edge=edge,
                )
            )
    return signals


def sort_and_limit(signals: List[Signal], max_alerts: int) -> List[Signal]:
    return sorted(signals, key=lambda s: s.edge, reverse=True)[:max_alerts]
