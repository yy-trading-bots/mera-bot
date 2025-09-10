from __future__ import annotations
from abc import ABC, abstractmethod
from typing import final, Any
from utils.logger import Logger
from bot.bot_settings import SETTINGS


class PositionState(ABC):
    """
    Abstract base class representing a trading position state.

    This class defines the interface and core workflow for handling position states.
    Each concrete state (e.g., Long, Short, Flat) must implement the `apply` method
    to define specific trading logic.
    """

    def __init__(self, parent: Any) -> None:
        """
        Initialize a PositionState.

        Args:
            parent (Any): The MeraBot object reference that manages trading logic,
                             containing shared resources like DataManager and BinanceAdapter.
        """
        self.parent: Any = parent

    @final
    def step(self) -> None:
        """
        Execute one step of the position state.

        This method refreshes market indicators and applies the logic
        of the current position state. It also includes exception handling
        to prevent interruptions in the trading loop.
        """
        try:
            self._refresh_indicators()
            if SETTINGS.DEBUG_MODE:
                Logger.log_info(
                    "debug: " + str(self.parent.data_manager.market_snapshot)
                )
            self.apply()
        except Exception as e:
            Logger.log_exception(str(e))

    @abstractmethod
    def apply(self) -> None:
        """
        Apply the trading logic for this position state.

        Subclasses must override this method to implement specific
        entry/exit conditions and state transitions.
        """
        pass

    def _refresh_indicators(self) -> None:
        """
        Refresh the latest market indicators.

        Updates the parent's DataManager with a fresh snapshot
        of indicators fetched from the BinanceAdapter.
        """
        self.parent.data_manager.market_snapshot = (
            self.parent.binance_adapter.indicator_manager.fetch_indicators()
        )
