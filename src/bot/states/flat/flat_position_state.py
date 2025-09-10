from __future__ import annotations

from bot.states.position_state import PositionState
from utils.logger import Logger
from tensorflow_model.tf_model import TFModel


class FlatPositionState(PositionState):
    """
    State representing the absence of any active position.

    This state evaluates entry conditions for LONG or SHORT positions
    using the latest market snapshot and transitions to the
    appropriate active-position state when conditions are satisfied.
    """

    def apply(self) -> None:
        """
        Evaluate entry conditions and transition to a new position state if met.

        When a LONG or SHORT entry condition is satisfied, the method delegates
        to the respective handler to open a position and update the bot state.
        """
        if self._is_long_entry_condition_met():
            self._apply_long(
                is_confirmed=(
                    TFModel().predict(self.parent.data_manager.market_snapshot)
                    == "LONG"
                )
            )
        elif self._is_short_entry_condition_met():
            self._apply_short(
                is_confirmed=(
                    TFModel().predict(self.parent.data_manager.market_snapshot)
                    == "SHORT"
                )
            )

    def _is_long_entry_condition_met(self) -> bool:
        """
        Check whether LONG entry conditions are satisfied.

        Returns:
            bool: True if LONG conditions are met; otherwise False.
        """
        snapshot = self.parent.data_manager.market_snapshot
        return (
            not self.parent.data_manager.is_long_blocked
            and snapshot.macd_12 > snapshot.macd_26
            and snapshot.macd_12 < 0
            and snapshot.rsi_6 > 50
            and snapshot.price < snapshot.ema_100
        )

    def _is_short_entry_condition_met(self) -> bool:
        """
        Check whether SHORT entry conditions are satisfied.

        Returns:
            bool: True if SHORT conditions are met; otherwise False.
        """
        snapshot = self.parent.data_manager.market_snapshot
        return (
            not self.parent.data_manager.is_short_blocked
            and snapshot.macd_12 < snapshot.macd_26
            and snapshot.macd_12 > 0
            and snapshot.rsi_6 < 50
            and snapshot.price > snapshot.ema_100
        )

    def _update_position_snapshot(self) -> None:
        """
        Persist the current market snapshot as the position snapshot.

        This is used to record the market context at the moment the position
        is opened (price and technical indicators).
        """
        self.parent.data_manager.position_snapshot = (
            self.parent.data_manager.market_snapshot.clone()
        )

    def _apply_long(self, is_confirmed: bool = False) -> None:
        """
        Enter a LONG position and transition to the LongPositionState.

        Actions performed:
            - Blocks further LONG entries until the position is closed.
            - Saves a position snapshot.
            - Places TP/SL via the exchange adapter (in non-test mode if confirmed).
            - Logs entry details.
        """
        self._update_position_snapshot()
        price: float = self.parent.data_manager.position_snapshot.price
        tp_price, sl_price = self.parent.binance_adapter.enter_long(
            price, state_block=(not is_confirmed)
        )

        if is_confirmed:
            Logger.log_info(
                "Entered LONG Current: "
                + str(round(price, 2))
                + " TP_PRICE: "
                + str(round(tp_price, 2))
                + " SL_PRICE: "
                + str(round(sl_price, 2))
            )
            Logger.log_info(str(self.parent.data_manager.position_snapshot))

        self.parent.data_manager.block_long()
        from bot.states.active.long_position_state import LongPositionState

        self.parent.state = LongPositionState(
            parent=self.parent, target_prices=[tp_price, sl_price]
        )

    def _apply_short(self, is_confirmed: bool) -> None:
        """
        Enter a SHORT position and transition to the ShortPositionState.

        Actions performed:
            - Blocks further SHORT entries until the position is closed.
            - Saves a position snapshot.
            - Places TP/SL via the exchange adapter (in non-test mode if confirmed).
            - Logs entry details.
        """
        self._update_position_snapshot()

        price: float = self.parent.data_manager.position_snapshot.price
        tp_price, sl_price = self.parent.binance_adapter.enter_short(
            price, state_block=(not is_confirmed)
        )

        if is_confirmed:
            Logger.log_info(
                "Entered SHORT Current: "
                + str(round(price, 2))
                + " TP_PRICE: "
                + str(round(tp_price, 2))
                + " SL_PRICE: "
                + str(round(sl_price, 2))
            )
            Logger.log_info(str(self.parent.data_manager.position_snapshot))

        self.parent.data_manager.block_short()
        from bot.states.active.short_position_state import ShortPositionState

        self.parent.state = ShortPositionState(
            parent=self.parent, target_prices=[tp_price, sl_price]
        )
