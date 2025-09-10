import pytest
from typing import Any, Literal, cast
from bot.states.active.active_position_state import ActivePositionState
import bot.states.active.active_position_state as open_pos_module
from bot.performance_tracker import PerformanceTracker

PositionSide = Literal["LONG", "SHORT"]


class FakeMarketSnapshot:
    def __init__(self, price: float = 0.0) -> None:
        self.price = price


class DataManager:
    def __init__(self) -> None:
        self.market_snapshot: Any | None = None
        self.position_snapshot: Any | None = None


class Parent:
    def __init__(self) -> None:
        self.data_manager = DataManager()
        self.performance_tracker = PerformanceTracker()
        self.state = None


class ConcreteOpen(ActivePositionState):
    def apply(self) -> None:
        return None

    def _is_tp_price(self) -> bool:
        return False

    def _is_sl_price(self) -> bool:
        return False


def test_init_sets_prices_as_float():
    parent = Parent()
    instance = ConcreteOpen(parent=parent, target_prices=[150.0, 80.0])
    assert isinstance(instance.tp_price, float) and instance.tp_price == 150.0
    assert isinstance(instance.sl_price, float) and instance.sl_price == 80.0


@pytest.mark.parametrize(
    "position,is_tp,expected",
    [
        ("LONG", True, "LONG"),
        ("LONG", False, "SHORT"),
        ("SHORT", True, "SHORT"),
        ("SHORT", False, "LONG"),
    ],
)
def test_get_position_result(position: PositionSide, is_tp: bool, expected: str):
    instance = ConcreteOpen(parent=Parent(), target_prices=[100.0, 90.0])
    assert instance._get_position_result(position=position, is_tp=is_tp) == expected


def test_handle_tp_increases_win_and_saves(monkeypatch):
    parent = Parent()
    instance = ConcreteOpen(parent=parent, target_prices=[100.0, 90.0])
    snapshot = FakeMarketSnapshot(price=123.0)

    success_logs: list[str] = []
    monkeypatch.setattr(
        open_pos_module.Logger, "log_success", lambda msg: success_logs.append(msg)
    )

    saved: dict[str, Any] = {}

    def fake_save_result(
        *, file_path: str, result: str, position: str, snapshot: Any
    ) -> None:
        saved["file_path"] = file_path
        saved["result"] = result
        saved["position"] = position
        saved["snapshot"] = snapshot

    monkeypatch.setattr(open_pos_module.FileUtils, "save_result", fake_save_result)

    tracker = PerformanceTracker()
    instance._handle_tp(
        position=cast(PositionSide, "LONG"),
        snapshot=cast(Any, snapshot),
        performance_tracker=tracker,
    )

    assert tracker.win_count == 1
    assert success_logs == ["Position is closed with TP"]
    assert saved["position"] == "LONG"
    assert saved["result"] == "LONG"
    assert saved["snapshot"] is snapshot


def test_handle_sl_increases_loss_and_saves(monkeypatch):
    parent = Parent()
    instance = ConcreteOpen(parent=parent, target_prices=[100.0, 90.0])
    snapshot = FakeMarketSnapshot(price=111.0)

    failure_logs: list[str] = []
    monkeypatch.setattr(
        open_pos_module.Logger, "log_failure", lambda msg: failure_logs.append(msg)
    )

    saved: dict[str, Any] = {}

    def fake_save_result(
        *, file_path: str, result: str, position: str, snapshot: Any
    ) -> None:
        saved["file_path"] = file_path
        saved["result"] = result
        saved["position"] = position
        saved["snapshot"] = snapshot

    monkeypatch.setattr(open_pos_module.FileUtils, "save_result", fake_save_result)

    tracker = PerformanceTracker()
    instance._handle_sl(
        position=cast(PositionSide, "SHORT"),
        snapshot=cast(Any, snapshot),
        performance_tracker=tracker,
    )

    assert tracker.loss_count == 1
    assert failure_logs == ["Position is closed with SL"]
    assert saved["position"] == "SHORT"
    assert saved["result"] == "LONG"
    assert saved["snapshot"] is snapshot


def test_close_position_calls_handler_logs_and_transitions(monkeypatch):
    parent = Parent()
    instance = ConcreteOpen(parent=parent, target_prices=[100.0, 90.0])

    entry_snapshot = FakeMarketSnapshot(price=99.0)
    parent.data_manager.position_snapshot = cast(Any, entry_snapshot)

    calls: dict[str, Any] = {}

    def handler(
        position: PositionSide, snapshot: Any, tracker: PerformanceTracker
    ) -> None:
        calls["position"] = position
        calls["snapshot"] = snapshot
        calls["tracker"] = tracker
        tracker.increase_win()

    info_logs: list[str] = []
    monkeypatch.setattr(
        open_pos_module.Logger, "log_info", lambda msg: info_logs.append(msg)
    )

    instance._close_position(
        position=cast(PositionSide, "LONG"), result_function=handler
    )

    assert calls["position"] == "LONG"
    assert calls["snapshot"] is entry_snapshot
    assert calls["tracker"] is parent.performance_tracker

    assert parent.state is not None
    assert parent.state.__class__.__name__ == "FlatPositionState"

    assert (
        info_logs
        and "TP:" in info_logs[0]
        and "SL:" in info_logs[0]
        and "Win-Rate:" in info_logs[0]
    )
