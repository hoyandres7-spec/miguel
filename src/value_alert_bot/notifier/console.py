from __future__ import annotations

from value_alert_bot.scoring import Signal


class ConsoleNotifier:
    def send(self, signal: Signal) -> None:
        selection_label = {
            "home": "LOCAL",
            "draw": "EMPATE",
            "away": "VISITANTE",
        }.get(signal.selection, signal.selection)

        message = (
            f"[ALERTA] {signal.home_team} vs {signal.away_team} | {signal.commence_time} | "
            f"1X2 | {selection_label}\n"
            f"Cuota: {signal.odds:.2f} (book: {signal.bookmaker})\n"
            f"P_modelo: {signal.p_model:.2f} | P_imp: {signal.p_implied:.2f} | "
            f"edge: {signal.edge * 100:.1f}%\n"
            "No es garantía; apuesta responsable."
        )
        print(message)
