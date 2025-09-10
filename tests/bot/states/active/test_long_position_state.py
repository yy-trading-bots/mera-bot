from bot.states.active.long_position_state import LongPositionState


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
    parent = Parent(price=101.0)
    lps = LongPositionState(parent=parent, target_prices=[100.0, 90.0])
    assert lps._is_tp_price() is True

    parent.data_manager.market_snapshot.price = 100.0
    assert lps._is_tp_price() is False


def test_is_sl_price_true_and_boundary():
    parent = Parent(price=89.0)
    lps = LongPositionState(parent=parent, target_prices=[150.0, 90.0])
    assert lps._is_sl_price() is True

    parent.data_manager.market_snapshot.price = 90.0
    assert lps._is_sl_price() is False


def test_apply_triggers_tp_branch(monkeypatch):
    parent = Parent(price=160.0)
    lps = LongPositionState(parent=parent, target_prices=[150.0, 80.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(lps, "_close_position", fake_close)
    lps.apply()

    assert calls["side"] == "LONG"
    assert calls["handler"].__name__ == "_handle_tp"
    assert getattr(calls["handler"], "__self__", None) is lps


def test_apply_triggers_sl_branch_when_no_tp(monkeypatch):
    parent = Parent(price=70.0)
    lps = LongPositionState(parent=parent, target_prices=[150.0, 80.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(lps, "_close_position", fake_close)
    lps.apply()

    assert calls["side"] == "LONG"
    assert calls["handler"].__name__ == "_handle_sl"
    assert getattr(calls["handler"], "__self__", None) is lps


def test_apply_no_action_when_neither_condition(monkeypatch):
    parent = Parent(price=120.0)
    lps = LongPositionState(parent=parent, target_prices=[150.0, 100.0])

    called = {"n": 0}

    def fake_close(*_args, **_kwargs):
        called["n"] += 1

    monkeypatch.setattr(lps, "_close_position", fake_close)
    lps.apply()

    assert called["n"] == 0


def test_apply_prefers_tp_when_both_true(monkeypatch):
    parent = Parent(price=150.0)
    lps = LongPositionState(parent=parent, target_prices=[100.0, 200.0])

    calls = {}

    def fake_close(side, handler):
        calls["side"] = side
        calls["handler"] = handler

    monkeypatch.setattr(lps, "_close_position", fake_close)
    lps.apply()

    assert calls["side"] == "LONG"
    assert calls["handler"].__name__ == "_handle_tp"
    assert getattr(calls["handler"], "__self__", None) is lps
