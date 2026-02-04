from value_alert_bot.scoring import implied_probabilities


def test_implied_probabilities_normalize() -> None:
    odds = {"home": 2.0, "draw": 3.0, "away": 4.0}
    implied = implied_probabilities(odds)
    total = sum(implied.values())
    assert abs(total - 1.0) < 1e-9
    assert implied["home"] > implied["away"]
