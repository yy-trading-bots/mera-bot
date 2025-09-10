from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
import pytest
from binance_adapter.binance_adapter import BinanceAdapter
import binance_adapter.binance_adapter as adapter_module


class FakeClient:
    """Replaces binance.client.Client inside the adapter module."""

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.futures_change_leverage: MagicMock = MagicMock()


class FakeAccountManager:
    """Account manager stub with MagicMock-typed attributes (helps Pylance)."""

    get_account_balance: MagicMock
    get_coin_amount: MagicMock
    enter_position: MagicMock
    place_tp_order: MagicMock
    place_sl_order: MagicMock

    def __init__(self, client):
        self.client = client
        self.get_account_balance = MagicMock(return_value=0.0)
        self.get_coin_amount = MagicMock(return_value=0.0)
        self.enter_position = MagicMock()
        self.place_tp_order = MagicMock()
        self.place_sl_order = MagicMock()


class FakeIndicatorManager:
    def __init__(self, client):
        self.client = client


@pytest.fixture
def base_settings():
    return SimpleNamespace(
        API_PUBLIC_KEY="pub",
        API_SECRET_KEY="sec",
        SYMBOL="BTCUSDT",
        LEVERAGE=20,
        TP_RATIO=0.02,
        SL_RATIO=0.01,
        COIN_PRECISION=2,
        TEST_MODE=True,
    )


@pytest.fixture(autouse=True)
def patch_module_symbols(monkeypatch, base_settings):
    monkeypatch.setattr(adapter_module, "SETTINGS", base_settings, raising=False)
    monkeypatch.setattr(adapter_module, "Client", FakeClient, raising=False)
    monkeypatch.setattr(
        adapter_module, "AccountManager", FakeAccountManager, raising=False
    )
    monkeypatch.setattr(
        adapter_module, "IndicatorManager", FakeIndicatorManager, raising=False
    )


def test_init_calls_leverage_when_not_in_test_mode(base_settings):
    base_settings.TEST_MODE = False
    adapter = BinanceAdapter()

    client = cast(FakeClient, adapter.client)
    account_manager = cast(FakeAccountManager, adapter.account_manager)
    indicator_manager = cast(FakeIndicatorManager, adapter.indicator_manager)

    assert isinstance(client, FakeClient)
    assert client.api_key == "pub"
    assert client.api_secret == "sec"
    assert isinstance(account_manager, FakeAccountManager)
    assert account_manager.client is client
    assert isinstance(indicator_manager, FakeIndicatorManager)
    assert indicator_manager.client is client

    client.futures_change_leverage.assert_called_once_with(
        symbol="BTCUSDT",
        leverage=20,
    )


def test_init_skips_leverage_in_test_mode(base_settings):
    base_settings.TEST_MODE = True
    adapter = BinanceAdapter()
    client = cast(FakeClient, adapter.client)
    client.futures_change_leverage.assert_not_called()


def test_enter_long_prices_no_orders_when_test_mode_true(base_settings):
    base_settings.TEST_MODE = True  # block order placement
    adapter = BinanceAdapter()
    account_manager = cast(FakeAccountManager, adapter.account_manager)

    account_manager.get_account_balance.return_value = 200.0

    captured = {}

    def get_coin_amount_spy(adjusted_balance, coin_price):
        captured["adjusted_balance"] = adjusted_balance
        captured["coin_price"] = coin_price
        return 0.5

    account_manager.get_coin_amount.side_effect = get_coin_amount_spy

    take_profit, stop_loss = adapter.enter_long(coin_price=100.0, state_block=False)

    assert captured["adjusted_balance"] == pytest.approx(200.0 * 0.95)
    assert captured["coin_price"] == pytest.approx(100.0)
    assert take_profit == pytest.approx(102.00)  # 100 * (1 + 0.02)
    assert stop_loss == pytest.approx(99.00)  # 100 * (1 - 0.01)

    account_manager.enter_position.assert_not_called()
    account_manager.place_tp_order.assert_not_called()
    account_manager.place_sl_order.assert_not_called()


def test_enter_long_prices_no_orders_when_state_block_true(base_settings):
    base_settings.TEST_MODE = False  # still blocked due to state_block=True
    adapter = BinanceAdapter()
    account_manager = cast(FakeAccountManager, adapter.account_manager)

    account_manager.get_account_balance.return_value = 150.0
    account_manager.get_coin_amount.return_value = 0.3

    take_profit, stop_loss = adapter.enter_long(coin_price=50.0, state_block=True)

    assert take_profit == pytest.approx(51.00)  # 50 * (1 + 0.02)
    assert stop_loss == pytest.approx(49.50)  # 50 * (1 - 0.01)

    account_manager.enter_position.assert_not_called()
    account_manager.place_tp_order.assert_not_called()
    account_manager.place_sl_order.assert_not_called()


def test_enter_short_prices_no_orders_when_test_mode_true(base_settings):
    base_settings.TEST_MODE = True
    adapter = BinanceAdapter()
    account_manager = cast(FakeAccountManager, adapter.account_manager)

    account_manager.get_account_balance.return_value = 80.0

    captured = {}

    def get_coin_amount_spy(adjusted_balance, coin_price):
        captured["adjusted_balance"] = adjusted_balance
        captured["coin_price"] = coin_price
        return 0.12

    account_manager.get_coin_amount.side_effect = get_coin_amount_spy

    take_profit, stop_loss = adapter.enter_short(coin_price=100.0, state_block=False)

    assert captured["adjusted_balance"] == pytest.approx(80.0 * 0.95)
    assert captured["coin_price"] == pytest.approx(100.0)
    assert take_profit == pytest.approx(98.00)  # 100 * (1 - 0.02)
    assert stop_loss == pytest.approx(101.00)  # 100 * (1 + 0.01)

    account_manager.enter_position.assert_not_called()
    account_manager.place_tp_order.assert_not_called()
    account_manager.place_sl_order.assert_not_called()


def test_enter_short_prices_no_orders_when_state_block_true(base_settings):
    base_settings.TEST_MODE = False
    adapter = BinanceAdapter()
    account_manager = cast(FakeAccountManager, adapter.account_manager)

    account_manager.get_account_balance.return_value = 500.0
    account_manager.get_coin_amount.return_value = 1.1

    take_profit, stop_loss = adapter.enter_short(coin_price=20.0, state_block=True)

    assert take_profit == pytest.approx(19.60)  # 20 * (1 - 0.02)
    assert stop_loss == pytest.approx(20.20)  # 20 * (1 + 0.01)

    account_manager.enter_position.assert_not_called()
    account_manager.place_tp_order.assert_not_called()
    account_manager.place_sl_order.assert_not_called()
