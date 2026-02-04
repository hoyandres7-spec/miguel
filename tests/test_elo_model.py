from value_alert_bot.config import EloConfig
from value_alert_bot.models.elo_soccer_1x2 import EloSoccer1X2


def test_elo_model_probabilities_sum_to_one() -> None:
    config = EloConfig(default_elo=1500, home_adv=60, base_draw=0.26, draw_decay=600)
    model = EloSoccer1X2(config)
    probs = model.probability_1x2("Arsenal", "Chelsea")
    total = probs.home_win + probs.draw + probs.away_win
    assert abs(total - 1.0) < 1e-9
    assert probs.home_win > 0
    assert probs.away_win > 0
