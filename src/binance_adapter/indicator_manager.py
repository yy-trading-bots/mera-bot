from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import numpy as np
import talib
import pandas as pd
from binance.client import Client
from bot.bot_settings import SETTINGS
from data.market_snapshot import MarketSnapshot
from utils.date_utils import DateUtils


class IndicatorManager:
    """
    Handles fetching historical market data from Binance
    and calculating technical indicators such as EMA, MACD, and RSI.
    """

    def __init__(self, client: Client) -> None:
        """
        Initialize the IndicatorManager.

        Args:
            client (Client): Binance Futures client instance used for API communication.
        """
        self.client: Client = client

    def _get_close_prices(self) -> np.ndarray:
        """
        Retrieve closing prices for the last month from Binance.

        Returns:
            np.ndarray: An array of closing prices.
        """
        klines = self.client.get_historical_klines(
            symbol=SETTINGS.SYMBOL,
            interval=SETTINGS.INTERVAL,
            start_str="1 month ago UTC",
        )
        df = pd.DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )
        return df["close"].astype(float).to_numpy()

    def _fetch_price(self) -> float:
        """
        Retrieve the current market price for the configured trading symbol.

        Returns:
            float: The latest price of the symbol. Returns 0.0 if unavailable.
        """
        ticker = self.client.get_symbol_ticker(symbol=SETTINGS.SYMBOL)
        if ticker:
            return float(ticker["price"])
        return 0.0

    def _calculate_EMA(
        self, period: int, close_prices: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate the Exponential Moving Average (EMA).

        Args:
            period (int): The lookback period for EMA.
            close_prices (Optional[np.ndarray], optional): Array of closing prices.
                If None, fresh data will be fetched. Defaults to None.

        Returns:
            float: The latest EMA value.
        """
        close_prices = (
            self._get_close_prices() if close_prices is None else close_prices
        )
        ema = talib.EMA(close_prices, timeperiod=period)
        return float(ema[-1])

    def _calculate_MACD(
        self,
        macd_period: int,
        signal_period: int,
        close_prices: Optional[np.ndarray] = None,
    ) -> Tuple[float, float]:
        """
        Calculate the Moving Average Convergence Divergence (MACD) indicator.

        Args:
            macd_period (int): Fast EMA period.
            signal_period (int): Slow EMA and signal line period.
            close_prices (Optional[np.ndarray], optional): Array of closing prices.
                If None, fresh data will be fetched. Defaults to None.

        Returns:
            Tuple[float, float]: Latest MACD and signal line values.
        """
        close_prices = (
            self._get_close_prices() if close_prices is None else close_prices
        )
        macd, signal, _ = talib.MACD(
            close_prices,
            fastperiod=macd_period,
            slowperiod=signal_period,
            signalperiod=signal_period,
        )
        return float(macd[-1]), float(signal[-1])

    def _calculate_RSI(
        self, period: int, close_prices: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate the Relative Strength Index (RSI).

        Args:
            period (int): The lookback period for RSI.
            close_prices (Optional[np.ndarray], optional): Array of closing prices.
                If None, fresh data will be fetched. Defaults to None.

        Returns:
            float: The latest RSI value.
        """
        close_prices = (
            self._get_close_prices() if close_prices is None else close_prices
        )
        rsi = talib.RSI(close_prices, timeperiod=period)
        return float(rsi[-1])

    def fetch_indicators(self) -> MarketSnapshot:
        """
        Fetch and calculate all configured indicators for the trading symbol.

        Returns:
            MarketSnapshot: Snapshot containing the latest price and indicators.
        """
        close_prices = self._get_close_prices()
        temp_macd_12, temp_macd_26 = self._calculate_MACD(
            macd_period=12, signal_period=26, close_prices=close_prices
        )

        return MarketSnapshot(
            date=DateUtils.get_date(),
            price=self._fetch_price(),
            macd_12=temp_macd_12,
            macd_26=temp_macd_26,
            ema_100=self._calculate_EMA(period=100, close_prices=close_prices),
            rsi_6=self._calculate_RSI(period=6, close_prices=close_prices),
        )
