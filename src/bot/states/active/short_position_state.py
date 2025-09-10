from __future__ import annotations
from bot.states.active.active_position_state import ActivePositionState


class ShortPositionState(ActivePositionState):
    """
    Represents an active SHORT trading position.

    This state continuously monitors whether the take-profit (TP)
    or stop-loss (SL) conditions are met. If one of these conditions
    is satisfied, it closes the position and updates the bot's state accordingly.
    """

    def apply(self) -> None:
        """
        Apply the logic for managing an active SHORT position.

        Responsibilities:
            - If TP price is reached, the position is closed with profit.
            - If SL price is reached, the position is closed with loss.
        """
        if self._is_tp_price():
            self._close_position("SHORT", self._handle_tp)

        elif self._is_sl_price():
            self._close_position("SHORT", self._handle_sl)

    def _is_tp_price(self) -> bool:
        """
        Check if the current market price has reached the take-profit (TP) threshold.

        Returns:
            bool: True if the current price is lower than the TP price; otherwise False.
        """
        snapshot = self.parent.data_manager.market_snapshot
        return snapshot.price < self.tp_price

    def _is_sl_price(self) -> bool:
        """
        Check if the current market price has reached the stop-loss (SL) threshold.

        Returns:
            bool: True if the current price is higher than the SL price; otherwise False.
        """
        snapshot = self.parent.data_manager.market_snapshot
        return snapshot.price > self.sl_price
