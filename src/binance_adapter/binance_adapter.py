from binance_adapter.account_manager import AccountManager
from bot.bot_settings import SETTINGS
from binance_adapter.indicator_manager import IndicatorManager
from binance.client import Client
from typing import Tuple


class BinanceAdapter:
    """
    Adapter class for interacting with Binance Futures API.
    Handles account operations (via AccountManager) and
    technical indicator fetching (via IndicatorManager).
    """

    def __init__(self) -> None:
        """
        Initialize the BinanceAdapter.

        Creates a Binance Futures client using API keys from settings and
        initializes account and indicator managers. If not in test mode,
        the client leverage is also configured.
        """
        self.client: Client = Client(SETTINGS.API_PUBLIC_KEY, SETTINGS.API_SECRET_KEY)
        self.account_manager: AccountManager = AccountManager(self.client)
        self.indicator_manager: IndicatorManager = IndicatorManager(self.client)

        if not SETTINGS.TEST_MODE:
            self.client.futures_change_leverage(
                symbol=SETTINGS.SYMBOL,
                leverage=SETTINGS.LEVERAGE,
            )

    def enter_long(
        self, coin_price: float, state_block: bool = False
    ) -> Tuple[float, float]:
        """
        Enter a LONG futures position. Calculates take-profit and stop-loss prices,
        places orders if not in test mode and not blocked.

        Args:
            coin_price (float): Current market price of the coin.
            state_block (bool, optional): Whether to block order placement. Defaults to False.

        Returns:
            Tuple[float, float]: A tuple containing (take_profit_price, stop_loss_price).
        """
        account_balance: float = self.account_manager.get_account_balance()
        coin_amount: float = self.account_manager.get_coin_amount(
            account_balance * 0.95, coin_price
        )

        tp_price: float = float(
            round(coin_price * (1 + SETTINGS.TP_RATIO), SETTINGS.COIN_PRECISION)
        )
        sl_price: float = float(
            round(coin_price * (1 - SETTINGS.SL_RATIO), SETTINGS.COIN_PRECISION)
        )

        if not SETTINGS.TEST_MODE and not state_block:
            self.account_manager.enter_position("LONG", coin_amount)
            self.account_manager.place_tp_order("LONG", coin_amount, tp_price)
            self.account_manager.place_sl_order("LONG", coin_amount, sl_price)

        return tp_price, sl_price

    def enter_short(
        self, coin_price: float, state_block: bool = False
    ) -> Tuple[float, float]:
        """
        Enter a SHORT futures position. Calculates take-profit and stop-loss prices,
        places orders if not in test mode and not blocked.

        Args:
            coin_price (float): Current market price of the coin.
            state_block (bool, optional): Whether to block order placement. Defaults to False.

        Returns:
            Tuple[float, float]: A tuple containing (take_profit_price, stop_loss_price).
        """
        account_balance: float = self.account_manager.get_account_balance()
        coin_amount: float = self.account_manager.get_coin_amount(
            account_balance * 0.95, coin_price
        )

        tp_price: float = float(
            round(coin_price * (1 - SETTINGS.TP_RATIO), SETTINGS.COIN_PRECISION)
        )
        sl_price: float = float(
            round(coin_price * (1 + SETTINGS.SL_RATIO), SETTINGS.COIN_PRECISION)
        )

        if not SETTINGS.TEST_MODE and not state_block:
            self.account_manager.enter_position("SHORT", coin_amount)
            self.account_manager.place_tp_order("SHORT", coin_amount, tp_price)
            self.account_manager.place_sl_order("SHORT", coin_amount, sl_price)

        return tp_price, sl_price
