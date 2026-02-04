from __future__ import annotations

import logging
from html import escape
from typing import Optional

import requests

from value_alert_bot.scoring import Signal
from value_alert_bot.utils import retry_with_backoff

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: float = 10.0) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def _format_message(self, signal: Signal) -> str:
        selection_label = {
            "home": "LOCAL",
            "draw": "EMPATE",
            "away": "VISITANTE",
        }.get(signal.selection, signal.selection)

        return (
            f"<b>ALERTA</b> {escape(signal.home_team)} vs {escape(signal.away_team)}\n"
            f"{escape(signal.commence_time)} | 1X2 | <b>{selection_label}</b>\n"
            f"Cuota: <b>{signal.odds:.2f}</b> (book: {escape(signal.bookmaker)})\n"
            f"P_modelo: {signal.p_model:.2f} | P_imp: {signal.p_implied:.2f} | "
            f"edge: {signal.edge * 100:.1f}%\n"
            "No es garantía; apuesta responsable."
        )

    def send(self, signal: Signal) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self._format_message(signal),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        def _request() -> Optional[dict]:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        retry_with_backoff(_request, logger=logger)
