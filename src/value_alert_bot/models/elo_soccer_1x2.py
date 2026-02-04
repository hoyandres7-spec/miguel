from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict

from value_alert_bot.config import EloConfig
from value_alert_bot.models.base import ModelOutcome, RatingModel


@dataclass
class EloSoccer1X2(RatingModel):
    config: EloConfig
    ratings: Dict[str, float] = field(default_factory=dict)
    model_version: str = "elo_soccer_1x2_v1"

    def _get_rating(self, team: str) -> float:
        return self.ratings.get(team, self.config.default_elo)

    def probability_1x2(self, home_team: str, away_team: str) -> ModelOutcome:
        elo_home = self._get_rating(home_team) + self.config.home_adv
        elo_away = self._get_rating(away_team)
        gap = elo_home - elo_away

        p_home_no_draw = 1.0 / (1.0 + 10 ** (-(gap) / 400.0))
        p_away_no_draw = 1.0 - p_home_no_draw

        draw = self.config.base_draw * math.exp(-abs(gap) / self.config.draw_decay)
        draw = min(max(draw, 0.0), 0.9)
        rest = max(0.0, 1.0 - draw)

        home_win = rest * p_home_no_draw
        away_win = rest * p_away_no_draw

        total = home_win + away_win + draw
        if total == 0:
            return ModelOutcome(home_win=0.0, draw=0.0, away_win=0.0)

        return ModelOutcome(
            home_win=home_win / total,
            draw=draw / total,
            away_win=away_win / total,
        )

    def get_ratings(self) -> Dict[str, float]:
        return dict(self.ratings)
