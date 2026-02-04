from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModelOutcome:
    home_win: float
    draw: float
    away_win: float


class RatingModel:
    model_version: str = "base"

    def probability_1x2(self, home_team: str, away_team: str) -> ModelOutcome:
        raise NotImplementedError

    def get_ratings(self) -> Dict[str, float]:
        return {}
