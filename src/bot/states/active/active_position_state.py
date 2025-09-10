from __future__ import annotations

from abc import abstractmethod
from typing import Callable, Sequence, Literal, Any
from bot.states.position_state import PositionState
from utils.logger import Logger
from utils.file_utils import FileUtils
from bot.bot_settings import SETTINGS
from data.market_snapshot import MarketSnapshot
from bot.performance_tracker import PerformanceTracker


class ActivePositionState(PositionState):
    """
    Base class for states that manage an active trading position.

    Subclasses (e.g., LongPositionState, ShortPositionState) must implement
    the price-condition checks for take-profit and stop-loss.
    """

    def __init__(self, parent: Any, target_prices: Sequence[float]) -> None:
        """
        Initialize the open position state.

        Args:
            parent (Any): The trading bot instance referance holding shared resources.
            target_prices (Sequence[float]): A 2-item sequence where index 0 is
                the take-profit price and index 1 is the stop-loss price.
        """
        super().__init__(parent)
        self.tp_price: float = float(target_prices[0])
        self.sl_price: float = float(target_prices[1])

    def _close_position(
        self,
        position: Literal["LONG", "SHORT"],
        result_function: Callable[
            [Literal["LONG", "SHORT"], MarketSnapshot, PerformanceTracker], None
        ],
    ) -> None:
        """
        Close the current position and transition back to FlatPositionState.

        Args:
            position (Literal["LONG", "SHORT"]): The side of the active position.
            result_function (Callable): Callback to handle result persistence
                and performance tracking (e.g., TP/SL handlers).

        Actions performed:
            - Invokes the given result handler (TP or SL).
            - Logs the updated win/loss statistics.
            - Transitions the bot state to FlatPositionState.
        """
        snapshot: MarketSnapshot = self.parent.data_manager.position_snapshot
        pf_tracker: PerformanceTracker = self.parent.performance_tracker

        result_function(position, snapshot, pf_tracker)

        Logger.log_info(
            "TP: "
            + str(pf_tracker.win_count)
            + " SL: "
            + str(pf_tracker.loss_count)
            + " Win-Rate: "
            + pf_tracker.calculate_win_rate()
        )

        from bot.states.flat.flat_position_state import FlatPositionState

        self.parent.state = FlatPositionState(parent=self.parent)

    def _handle_tp(
        self,
        position: Literal["LONG", "SHORT"],
        snapshot: MarketSnapshot,
        performance_tracker: PerformanceTracker,
    ) -> None:
        """
        Handle a position closed by take-profit.

        Args:
            position (Literal["LONG", "SHORT"]): The side of the closed position.
            snapshot (MarketSnapshot): Snapshot at the time of entry.
            performance_tracker (PerformanceTracker): Tracker for wins/losses.

        Actions performed:
            - Increments win count.
            - Persists the TP result to CSV.
            - Logs the outcome.
        """
        Logger.log_success("Position is closed with TP")
        performance_tracker.increase_win()
        FileUtils.save_result(
            file_path=SETTINGS.OUTPUT_CSV_PATH,
            result=self._get_position_result(position=position, is_tp=True),
            position=position,
            snapshot=snapshot,
        )

    def _handle_sl(
        self,
        position: Literal["LONG", "SHORT"],
        snapshot: MarketSnapshot,
        performance_tracker: PerformanceTracker,
    ) -> None:
        """
        Handle a position closed by stop-loss.

        Args:
            position (Literal["LONG", "SHORT"]): The side of the closed position.
            snapshot (MarketSnapshot): Snapshot at the time of entry.
            performance_tracker (PerformanceTracker): Tracker for wins/losses.

        Actions performed:
            - Increments loss count.
            - Persists the SL result to CSV.
            - Logs the outcome.
        """
        Logger.log_failure("Position is closed with SL")
        performance_tracker.increase_loss()
        FileUtils.save_result(
            file_path=SETTINGS.OUTPUT_CSV_PATH,
            result=self._get_position_result(position=position, is_tp=False),
            position=position,
            snapshot=snapshot,
        )

    def _get_position_result(
        self, position: Literal["LONG", "SHORT"], is_tp: bool
    ) -> str:
        """
        Convert a position side and TP/SL flag into a result label.

        Args:
            position (Literal["LONG", "SHORT"]): The side of the position.
            is_tp (bool): True if closed by TP; False if closed by SL.

        Returns:
            str: The result label to be stored (original side for TP,
                 reversed side for SL).
        """
        reversed_position: str = "SHORT" if position == "LONG" else "LONG"
        return position if is_tp else reversed_position

    @abstractmethod
    def _is_tp_price(self) -> bool:
        """
        Indicate whether the take-profit level has been reached.

        Returns:
            bool: True if TP condition is met; otherwise False.
        """
        raise NotImplementedError

    @abstractmethod
    def _is_sl_price(self) -> bool:
        """
        Indicate whether the stop-loss level has been reached.

        Returns:
            bool: True if SL condition is met; otherwise False.
        """
        raise NotImplementedError
