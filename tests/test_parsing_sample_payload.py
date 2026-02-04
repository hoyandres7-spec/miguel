import json
from pathlib import Path

from value_alert_bot.odds_api import parse_events


def test_parse_events_from_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "odds_sample.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    events = parse_events(payload)
    assert len(events) == 1
    event = events[0]
    assert event.home_team == "Arsenal"
    assert event.away_team == "Chelsea"
    assert event.odds_home is not None
    assert event.odds_draw is not None
    assert event.odds_away is not None
    assert event.odds_home.odds == 2.1
    assert event.odds_draw.odds == 3.5
