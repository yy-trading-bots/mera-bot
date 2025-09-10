from data.market_snapshot import MarketSnapshot
from utils.logger import Logger


class DataManager:
    """
    Manages indicator and position snapshots along with trading state flags.

    This class tracks whether LONG or SHORT positions are currently blocked,
    stores the latest market indicator snapshot, and keeps the snapshot
    taken at the time a position is opened.
    """

    def __init__(self) -> None:
        """
        Initialize the DataManager.

        Attributes:
            is_long_blocked (bool): Flag indicating whether LONG entries are blocked.
            is_short_blocked (bool): Flag indicating whether SHORT entries are blocked.
            market_snapshot (MarketSnapshot): Latest fetched market indicators.
            position_snapshot (MarketSnapshot): Snapshot of the market
                at the moment a position is opened.
        """
        self.is_long_blocked: bool = False
        self.is_short_blocked: bool = False
        self.market_snapshot: MarketSnapshot
        self.position_snapshot: MarketSnapshot

    def block_short(self) -> None:
        """
        Block SHORT entries and unblock LONG entries.

        Actions:
            - Sets the SHORT blocked flag to True.
            - Logs the SHORT trading block event.
            - Sets the LONG blocked flag to False.
            - Logs the LONG trading unblock event.
        """
        self.is_short_blocked = True
        Logger.log_info("SHORT trading is BLOCKED.")
        self.is_long_blocked = False
        Logger.log_info("LONG trading is UNBLOCKED.")

    def block_long(self) -> None:
        """
        Block LONG entries and unblock SHORT entries.

        Actions:
            - Sets the LONG blocked flag to True.
            - Logs the LONG trading block event.
            - Sets the SHORT blocked flag to False.
            - Logs the SHORT trading unblock event.
        """
        self.is_long_blocked = True
        Logger.log_info("Long trading is BLOCKED.")
        self.is_short_blocked = False
        Logger.log_info("Short trading is UNBLOCKED.")
