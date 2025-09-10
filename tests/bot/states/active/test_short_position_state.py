from bot.states.active.short_position_state import ShortPositionState


class Snapshot:
    def __init__(self, price: float) -> None:
        self.price = price


class DataManager:
    def __init__(self, snapshot: Snapshot) -> None:
        self.market_snapshot = snapshot


class Parent:
    def __init__(self, price: float) -> None:
        self.data_manager = DataManager(Snapshot(price))


def test_is_tp_price_true_and_boundary():
    parent = Parent(price=79.0)
    sps = ShortPositionState(parent=parent, target_prices=[80.0, 120.0])
    assert sps._is_tp_price() is True

    parent.data_manager.market_snapshot.price = 80.0
    assert sps._is_tp_price() is False


def test_is_sl_price_true_and_boundary():
    parent = Parent(price=121.0)
    sps = ShortPositionState(parent=parent, target_prices=[80.0, 120.0])
    assert sps._is_sl_price() is True

    parent.data_manager.market_snapshot.price = 120.0
    assert sps._is_sl_price() is False


def test_apply_triggers_tp_branch(monkeypatch):
    parent = Parent(price=70.0)
    sps = ShortPositionState(parent=parent, target_prices=[80.0, 120.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(sps, "_close_position", fake_close)
    sps.apply()

    assert calls["side"] == "SHORT"
    assert calls["handler"].__name__ == "_handle_tp"
    assert getattr(calls["handler"], "__self__", None) is sps


def test_apply_triggers_sl_branch_when_no_tp(monkeypatch):
    parent = Parent(price=130.0)
    sps = ShortPositionState(parent=parent, target_prices=[80.0, 120.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(sps, "_close_position", fake_close)
    sps.apply()

    assert calls["side"] == "SHORT"
    assert calls["handler"].__name__ == "_handle_sl"
    assert getattr(calls["handler"], "__self__", None) is sps


def test_apply_no_action_when_neither_condition(monkeypatch):
    parent = Parent(price=100.0)
    # Choose thresholds so both checks are False:
    # price < tp_price  -> 100 < 80  => False
    # price > sl_price  -> 100 > 120 => False
    sps = ShortPositionState(parent=parent, target_prices=[80.0, 120.0])

    called = {"n": 0}

    def fake_close(*_args, **_kwargs):
        called["n"] += 1

    monkeypatch.setattr(sps, "_close_position", fake_close)
    sps.apply()

    assert called["n"] == 0


def test_apply_prefers_tp_when_both_true(monkeypatch):
    parent = Parent(price=100.0)  # price < tp and price > sl ⇒ both true
    sps = ShortPositionState(parent=parent, target_prices=[120.0, 80.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(sps, "_close_position", fake_close)
    sps.apply()

    assert calls["side"] == "SHORT"
    assert calls["handler"].__name__ == "_handle_tp"
    assert getattr(calls["handler"], "__self__", None) is sps
