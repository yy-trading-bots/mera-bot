from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from binance_adapter.account_manager import AccountManager
import binance_adapter.account_manager as account_manager_module


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    fake_settings = SimpleNamespace(LEVERAGE="10", SYMBOL="BTCUSDT")
    monkeypatch.setattr(
        account_manager_module, "SETTINGS", fake_settings, raising=False
    )
    yield


@pytest.fixture
def client():
    mock_binance_client = MagicMock()
    mock_binance_client.futures_account_balance.return_value = []
    return mock_binance_client


def test_init_stores_client(client):
    account_manager = AccountManager(client)
    assert account_manager.client is client


def test_get_coin_amount_uses_leverage(client):
    account_manager = AccountManager(client)
    assert account_manager.get_coin_amount(balance=100.0, price=200.0) == pytest.approx(
        5.0
    )


def test_get_account_balance_returns_usdt_when_present(client):
    client.futures_account_balance.return_value = [
        {"asset": "BTC", "balance": "0.01"},
        {"asset": "USDT", "balance": "123.45"},
        {"asset": "ETH", "balance": "2.0"},
    ]
    account_manager = AccountManager(client)
    assert account_manager.get_account_balance() == pytest.approx(123.45)


def test_get_account_balance_returns_zero_when_missing(client):
    client.futures_account_balance.return_value = [
        {"asset": "BUSD", "balance": "50"},
        {"asset": "ETH", "balance": "2.0"},
    ]
    account_manager = AccountManager(client)
    assert account_manager.get_account_balance() == 0.0


def test_enter_position_long_places_buy_long_market_order(client):
    account_manager = AccountManager(client)
    account_manager.enter_position(order_type="LONG", quantity=1.23)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs == {
        "symbol": "BTCUSDT",
        "quantity": 1.23,
        "type": "MARKET",
        "side": "BUY",
        "positionSide": "LONG",
    }


def test_enter_position_short_places_sell_short_market_order(client):
    account_manager = AccountManager(client)
    account_manager.enter_position(order_type="SHORT", quantity=2.0)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs == {
        "symbol": "BTCUSDT",
        "quantity": 2.0,
        "type": "MARKET",
        "side": "SELL",
        "positionSide": "SHORT",
    }


def test_place_tp_order_long_builds_correct_payload(client):
    account_manager = AccountManager(client)
    account_manager.place_tp_order(order_type="LONG", quantity=0.5, tp_price=25000.0)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs == {
        "symbol": "BTCUSDT",
        "quantity": 0.5,
        "type": "TAKE_PROFIT_MARKET",
        "positionSide": "LONG",
        "firstTrigger": "PLACE_ORDER",
        "timeInForce": "GTE_GTC",
        "stopPrice": 25000.0,
        "side": "SELL",
        "secondTrigger": "CANCEL_ORDER",
        "workingType": "MARK_PRICE",
        "priceProtect": "true",
    }


def test_place_tp_order_short_builds_correct_payload(client):
    account_manager = AccountManager(client)
    account_manager.place_tp_order(order_type="SHORT", quantity=0.75, tp_price=20000.0)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs["type"] == "TAKE_PROFIT_MARKET"
    assert order_kwargs["positionSide"] == "SHORT"
    assert order_kwargs["side"] == "BUY"
    assert order_kwargs["symbol"] == "BTCUSDT"
    assert order_kwargs["quantity"] == 0.75
    assert order_kwargs["stopPrice"] == 20000.0
    assert order_kwargs["firstTrigger"] == "PLACE_ORDER"
    assert order_kwargs["secondTrigger"] == "CANCEL_ORDER"
    assert order_kwargs["workingType"] == "MARK_PRICE"
    assert order_kwargs["timeInForce"] == "GTE_GTC"
    assert order_kwargs["priceProtect"] == "true"


def test_place_sl_order_long_builds_correct_payload(client):
    account_manager = AccountManager(client)
    account_manager.place_sl_order(order_type="LONG", quantity=1.0, sl_price=19000.0)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs == {
        "symbol": "BTCUSDT",
        "quantity": 1.0,
        "type": "STOP_MARKET",
        "positionSide": "LONG",
        "firstTrigger": "PLACE_ORDER",
        "timeInForce": "GTE_GTC",
        "stopPrice": 19000.0,
        "side": "SELL",
        "secondTrigger": "CANCEL_ORDER",
        "workingType": "MARK_PRICE",
        "priceProtect": "true",
    }


def test_place_sl_order_short_builds_correct_payload(client):
    account_manager = AccountManager(client)
    account_manager.place_sl_order(order_type="SHORT", quantity=3.0, sl_price=31000.0)
    order_kwargs = client.futures_create_order.call_args.kwargs
    assert order_kwargs["type"] == "STOP_MARKET"
    assert order_kwargs["positionSide"] == "SHORT"
    assert order_kwargs["side"] == "BUY"
    assert order_kwargs["symbol"] == "BTCUSDT"
    assert order_kwargs["quantity"] == 3.0
    assert order_kwargs["stopPrice"] == 31000.0
    assert order_kwargs["firstTrigger"] == "PLACE_ORDER"
    assert order_kwargs["secondTrigger"] == "CANCEL_ORDER"
    assert order_kwargs["workingType"] == "MARK_PRICE"
    assert order_kwargs["timeInForce"] == "GTE_GTC"
    assert order_kwargs["priceProtect"] == "true"
