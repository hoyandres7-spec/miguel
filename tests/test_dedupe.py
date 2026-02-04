from pathlib import Path

from value_alert_bot.dedupe import DedupeStore, build_hash


def test_dedupe_store(tmp_path: Path) -> None:
    db_path = tmp_path / "dedupe.sqlite"
    store = DedupeStore(str(db_path), ttl_hours=24)
    hash_value = build_hash("event", "market", "home", "book", "2.0", "model")

    assert store.seen(hash_value) is False
    store.add(hash_value)
    assert store.seen(hash_value) is True
