from bot.bot_settings import SETTINGS
from binance.client import Client


class AccountManager:
    """
    Manages account operations such as retrieving balances,
    calculating order quantities, and placing futures orders
    (market, take-profit, and stop-loss) on Binance.
    """

    def __init__(self, client: Client) -> None:
        """
        Initialize the AccountManager.

        Args:
            client (Client): Binance Futures client instance used for API communication.
        """
        self.client: Client = client

    def get_coin_amount(self, balance: float, price: float) -> float:
        """
        Calculate the quantity of coins to buy/sell based on account balance, price, and leverage.

        Args:
            balance (float): Available balance in USDT.
            price (float): Current price of the coin.

        Returns:
            float: Calculated coin amount.
        """
        notional: float = balance * float(SETTINGS.LEVERAGE)
        return notional / price

    def get_account_balance(self) -> float:
        """
        Retrieve the USDT balance from the futures account.

        Returns:
            float: Available USDT balance. Returns 0.0 if not found.
        """
        account_info = self.client.futures_account_balance()
        for item in account_info:
            if item["asset"] == "USDT":
                return float(item["balance"])
        return 0.0

    def enter_position(self, order_type: str, quantity: float) -> None:
        """
        Enter a futures position (LONG or SHORT) using a market order.

        Args:
            order_type (str): Type of position ("LONG" or "SHORT").
            quantity (float): Quantity of the asset to trade.
        """
        side, position = ("BUY", "LONG") if order_type == "LONG" else ("SELL", "SHORT")

        self.client.futures_create_order(
            symbol=SETTINGS.SYMBOL,
            quantity=quantity,
            type="MARKET",
            side=side,
            positionSide=position,
        )

    def place_tp_order(self, order_type: str, quantity: float, tp_price: float) -> None:
        """
        Place a Take-Profit (TP) market order for an open position.

        Args:
            order_type (str): Type of position ("LONG" or "SHORT").
            quantity (float): Quantity of the asset.
            tp_price (float): Price at which to trigger the TP order.
        """
        side, position = ("SELL", "LONG") if order_type == "LONG" else ("BUY", "SHORT")

        self.client.futures_create_order(
            symbol=SETTINGS.SYMBOL,
            quantity=quantity,
            type="TAKE_PROFIT_MARKET",
            positionSide=position,
            firstTrigger="PLACE_ORDER",
            timeInForce="GTE_GTC",
            stopPrice=tp_price,
            side=side,
            secondTrigger="CANCEL_ORDER",
            workingType="MARK_PRICE",
            priceProtect="true",
        )

    def place_sl_order(self, order_type: str, quantity: float, sl_price: float) -> None:
        """
        Place a Stop-Loss (SL) market order for an open position.

        Args:
            order_type (str): Type of position ("LONG" or "SHORT").
            quantity (float): Quantity of the asset.
            sl_price (float): Price at which to trigger the SL order.
        """
        side, position = ("SELL", "LONG") if order_type == "LONG" else ("BUY", "SHORT")

        self.client.futures_create_order(
            symbol=SETTINGS.SYMBOL,
            quantity=quantity,
            type="STOP_MARKET",
            positionSide=position,
            firstTrigger="PLACE_ORDER",
            timeInForce="GTE_GTC",
            stopPrice=sl_price,
            side=side,
            secondTrigger="CANCEL_ORDER",
            workingType="MARK_PRICE",
            priceProtect="true",
        )
