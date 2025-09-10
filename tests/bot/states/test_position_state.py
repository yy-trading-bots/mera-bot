from bot.states.position_state import PositionState
import bot.states.position_state as position_state_module


class Snapshot:
    def __init__(self, price: float = 0.0, ema_100: float = 0.0) -> None:
        self.price = price
        self.ema_100 = ema_100


class DummyIndicatorManager:
    def __init__(self, snapshot: Snapshot) -> None:
        self._snapshot = snapshot
        self.calls = []

    def fetch_indicators(self) -> Snapshot:
        self.calls.append("fetch")
        return self._snapshot


class DummyBinanceAdapter:
    def __init__(self, snapshot: Snapshot) -> None:
        self.indicator_manager = DummyIndicatorManager(snapshot)


class DummyDataManager:
    def __init__(self) -> None:
        self.market_snapshot = None


class ConcreteState(PositionState):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.calls = []

    def apply(self) -> None:
        self.calls.append("apply")


class RaisingApplyState(PositionState):
    def apply(self) -> None:
        raise ValueError("boom")


def make_parent(snapshot: Snapshot):
    class Parent:
        def __init__(self, s: Snapshot) -> None:
            self.data_manager = DummyDataManager()
            self.binance_adapter = DummyBinanceAdapter(s)

    return Parent(snapshot)


def test_step_refreshes_indicators_then_calls_apply(monkeypatch):
    snapshot = Snapshot(price=1.0, ema_100=2.0)
    parent = make_parent(snapshot)
    state = ConcreteState(parent)

    logged = []
    monkeypatch.setattr(
        position_state_module.Logger, "log_exception", lambda msg: logged.append(msg)
    )

    state.step()

    assert parent.data_manager.market_snapshot is snapshot
    assert parent.binance_adapter.indicator_manager.calls == ["fetch"]
    assert state.calls == ["apply"]
    assert logged == []


def test_step_logs_when_apply_raises(monkeypatch):
    snapshot = Snapshot(price=3.0, ema_100=4.0)
    parent = make_parent(snapshot)
    state = RaisingApplyState(parent)

    logged = []
    monkeypatch.setattr(
        position_state_module.Logger, "log_exception", lambda msg: logged.append(msg)
    )

    state.step()

    assert parent.data_manager.market_snapshot is snapshot
    assert logged == ["boom"]


def test_step_logs_when_refresh_raises(monkeypatch):
    snapshot = Snapshot()
    parent = make_parent(snapshot)

    def raise_on_fetch():
        raise RuntimeError("net down")

    monkeypatch.setattr(
        parent.binance_adapter.indicator_manager, "fetch_indicators", raise_on_fetch
    )

    state = ConcreteState(parent)

    logged = []
    monkeypatch.setattr(
        position_state_module.Logger, "log_exception", lambda msg: logged.append(msg)
    )

    state.step()

    assert parent.data_manager.market_snapshot is None
    assert logged == ["net down"]


def test_refresh_indicators_sets_parent_snapshot():
    snapshot = Snapshot(price=10.0, ema_100=9.0)
    parent = make_parent(snapshot)
    state = ConcreteState(parent)

    assert parent.data_manager.market_snapshot is None
    state._refresh_indicators()
    assert parent.data_manager.market_snapshot is snapshot
