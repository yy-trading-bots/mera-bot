from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
import numpy as np
import pytest
from binance_adapter.indicator_manager import IndicatorManager
import binance_adapter.indicator_manager as indicator_manager_module


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    fake_settings = SimpleNamespace(
        SYMBOL="BTCUSDT",
        INTERVAL="1m",
    )
    monkeypatch.setattr(
        indicator_manager_module, "SETTINGS", fake_settings, raising=False
    )


@pytest.fixture
def binance_client_mock():
    client = MagicMock()
    client.get_historical_klines.return_value = []
    client.get_klines.return_value = []
    client.get_symbol_ticker.return_value = {"price": "0"}
    return client


def test_get_close_prices_returns_numpy_array(binance_client_mock):
    # Binance returns raw klines; only "close" column is used.
    klines = [
        # open time, open, high, low, close, volume, close_time, quote_asset_volume, number_of_trades,
        # taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore
        [0, "100", "110", "90", "105.5", "1", 0, "0", "0", "0", "0", "0"],
        [0, "105", "115", "100", "111.7", "1", 0, "0", "0", "0", "0", "0"],
    ]
    binance_client_mock.get_historical_klines.return_value = klines

    indicator_manager = IndicatorManager(binance_client_mock)
    close_prices = indicator_manager._get_close_prices()

    assert isinstance(close_prices, np.ndarray)
    assert close_prices.tolist() == [105.5, 111.7]
    binance_client_mock.get_historical_klines.assert_called_once_with(
        symbol="BTCUSDT",
        interval="1m",
        start_str="1 month ago UTC",
    )


def test_fetch_price_returns_float(binance_client_mock):
    binance_client_mock.get_symbol_ticker.return_value = {"price": "123.45"}
    indicator_manager = IndicatorManager(binance_client_mock)
    latest_price = indicator_manager._fetch_price()
    assert latest_price == pytest.approx(123.45)


def test_fetch_price_returns_zero_when_unavailable(binance_client_mock):
    binance_client_mock.get_symbol_ticker.return_value = None
    indicator_manager = IndicatorManager(binance_client_mock)
    assert indicator_manager._fetch_price() == 0.0


def test_calculate_ema_with_provided_closes(monkeypatch, binance_client_mock):
    # Stub talib.EMA to return an array whose last element is distinctive
    def fake_ema(arr, timeperiod):
        return np.array([0.0] * (len(arr) - 1) + [42.0])

    monkeypatch.setattr(indicator_manager_module.talib, "EMA", fake_ema)

    indicator_manager = IndicatorManager(binance_client_mock)
    value = indicator_manager._calculate_EMA(
        period=100, close_prices=np.array([1.0, 2.0, 3.0])
    )
    assert value == pytest.approx(42.0)


def test_calculate_ema_fetches_when_none(monkeypatch, binance_client_mock):
    def fake_ema(arr, timeperiod):
        return np.array([0.0] * (len(arr) - 1) + [99.0])

    monkeypatch.setattr(indicator_manager_module.talib, "EMA", fake_ema)

    indicator_manager = IndicatorManager(binance_client_mock)
    # Ensure it fetches by patching _get_close_prices
    monkeypatch.setattr(
        indicator_manager, "_get_close_prices", lambda: np.array([5.0, 6.0, 7.0])
    )
    value = indicator_manager._calculate_EMA(period=100, close_prices=None)
    assert value == pytest.approx(99.0)


def test_calculate_macd_with_provided_closes(monkeypatch, binance_client_mock):
    def fake_macd(arr, fastperiod, slowperiod, signalperiod):
        length = len(arr)
        return (
            np.array([0.0] * (length - 1) + [1.1]),
            np.array([0.0] * (length - 1) + [2.2]),
            np.array([0.0] * (length - 1) + [3.3]),
        )

    monkeypatch.setattr(indicator_manager_module.talib, "MACD", fake_macd)

    indicator_manager = IndicatorManager(binance_client_mock)
    macd_value, signal_value = indicator_manager._calculate_MACD(
        macd_period=12, signal_period=26, close_prices=np.array([1.0, 2.0, 3.0])
    )
    assert macd_value == pytest.approx(1.1)
    assert signal_value == pytest.approx(2.2)


def test_calculate_macd_fetches_when_none_and_params_are_passed(
    monkeypatch, binance_client_mock
):
    captured = {}

    def spy_macd(arr, fastperiod, slowperiod, signalperiod):
        captured["len"] = len(arr)
        captured["fastperiod"] = fastperiod
        captured["slowperiod"] = slowperiod
        captured["signalperiod"] = signalperiod
        return (
            np.array([0.0, 9.9]),
            np.array([0.0, 8.8]),
            np.array([0.0, 7.7]),
        )

    monkeypatch.setattr(indicator_manager_module.talib, "MACD", spy_macd)

    indicator_manager = IndicatorManager(binance_client_mock)
    monkeypatch.setattr(
        indicator_manager, "_get_close_prices", lambda: np.array([10.0, 20.0])
    )

    macd_value, signal_value = indicator_manager._calculate_MACD(
        macd_period=12, signal_period=26, close_prices=None
    )

    assert macd_value == pytest.approx(9.9)
    assert signal_value == pytest.approx(8.8)
    assert captured["len"] == 2
    assert captured["fastperiod"] == 12
    assert captured["slowperiod"] == 26
    assert captured["signalperiod"] == 26


def test_calculate_rsi_with_and_without_fetch(monkeypatch, binance_client_mock):
    def fake_rsi(arr, timeperiod):
        return np.array([0.0] * (len(arr) - 1) + [55.5])

    monkeypatch.setattr(indicator_manager_module.talib, "RSI", fake_rsi)

    indicator_manager = IndicatorManager(binance_client_mock)
    # with provided closes
    provided_value = indicator_manager._calculate_RSI(
        period=6, close_prices=np.array([1.0, 2.0, 3.0])
    )
    assert provided_value == pytest.approx(55.5)

    # fetch branch
    monkeypatch.setattr(
        indicator_manager, "_get_close_prices", lambda: np.array([4.0, 5.0, 6.0])
    )
    fetched_value = indicator_manager._calculate_RSI(period=6, close_prices=None)
    assert fetched_value == pytest.approx(55.5)


def test_fetch_indicators_integration_and_constructor_call(
    monkeypatch, binance_client_mock
):
    # Spy on the internal calls and verify parameters used in fetch_indicators
    indicator_manager = IndicatorManager(binance_client_mock)

    monkeypatch.setattr(
        indicator_manager, "_get_close_prices", lambda: np.array([1.0, 2.0, 3.0])
    )

    captured_params = {}

    def spy_macd(macd_period, signal_period, close_prices):
        captured_params["macd_period"] = macd_period
        captured_params["signal_period"] = signal_period
        captured_params["macd_close_len"] = len(close_prices)
        return 1.1, 2.2

    def spy_ema(period, close_prices):
        captured_params["ema_period"] = period
        captured_params["ema_close_len"] = len(close_prices)
        return 100.5

    def spy_rsi(period, close_prices):
        captured_params["rsi_period"] = period
        captured_params["rsi_close_len"] = len(close_prices)
        return 55.5

    def spy_price():
        return 555.0

    monkeypatch.setattr(indicator_manager, "_calculate_MACD", spy_macd)
    monkeypatch.setattr(indicator_manager, "_calculate_EMA", spy_ema)
    monkeypatch.setattr(indicator_manager, "_calculate_RSI", spy_rsi)
    monkeypatch.setattr(indicator_manager, "_fetch_price", lambda: spy_price())

    # Fix date
    monkeypatch.setattr(
        indicator_manager_module.DateUtils, "get_date", lambda: "2025-08-27T00:00:00Z"
    )

    # Replace MarketSnapshot to capture constructor kwargs
    class FakeSnapshot:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(
        indicator_manager_module, "MarketSnapshot", FakeSnapshot, raising=False
    )

    snapshot = indicator_manager.fetch_indicators()
    assert isinstance(snapshot, FakeSnapshot)

    # Verify internal call parameters
    assert captured_params["macd_period"] == 12
    assert captured_params["signal_period"] == 26
    assert captured_params["ema_period"] == 100
    assert captured_params["rsi_period"] == 6
    assert captured_params["macd_close_len"] == 3
    assert captured_params["ema_close_len"] == 3
    assert captured_params["rsi_close_len"] == 3

    # Verify fields passed to MarketSnapshot
    expected = {
        "date": "2025-08-27T00:00:00Z",
        "price": 555.0,
        "macd_12": 1.1,
        "macd_26": 2.2,
        "ema_100": 100.5,
        "rsi_6": 55.5,
    }
    assert snapshot.kwargs == expected
