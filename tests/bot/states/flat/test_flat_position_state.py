import types
import builtins
import pytest

from bot.states.flat.flat_position_state import FlatPositionState
import bot.states.flat.flat_position_state as flat_pos_module


class DummySnapshot:
    def __init__(
        self,
        price: float = 100.0,
        ema_100: float = 120.0,
        macd_12: float = 0.0,
        macd_26: float = 0.0,
        rsi_6: float = 50.0,
    ) -> None:
        self.price = price
        self.ema_100 = ema_100
        self.macd_12 = macd_12
        self.macd_26 = macd_26
        self.rsi_6 = rsi_6
        self._cloned = False

    def clone(self) -> "DummySnapshot":
        cloned = DummySnapshot(
            price=self.price,
            ema_100=self.ema_100,
            macd_12=self.macd_12,
            macd_26=self.macd_26,
            rsi_6=self.rsi_6,
        )
        cloned._cloned = True
        return cloned

    def __str__(self) -> str:
        return f"Snapshot(price={self.price})"


class DummyDataManager:
    def __init__(self, snapshot: DummySnapshot) -> None:
        self.market_snapshot = snapshot
        self.position_snapshot = None
        self.is_long_blocked = False
        self.is_short_blocked = False

    def block_long(self) -> None:
        self.is_long_blocked = True

    def block_short(self) -> None:
        self.is_short_blocked = True


class DummyBinanceAdapter:
    def __init__(
        self, long_tp=110.0, long_sl=90.0, short_tp=80.0, short_sl=120.0
    ) -> None:
        self._long_tp = long_tp
        self._long_sl = long_sl
        self._short_tp = short_tp
        self._short_sl = short_sl
        self.called: dict[str, tuple[float, bool]] = {}

    def enter_long(self, price: float, state_block: bool = False):
        self.called["enter_long"] = (price, state_block)
        return self._long_tp, self._long_sl

    def enter_short(self, price: float, state_block: bool = False):
        self.called["enter_short"] = (price, state_block)
        return self._short_tp, self._short_sl


class DummyParent:
    def __init__(
        self, snapshot: DummySnapshot, adapter: DummyBinanceAdapter | None = None
    ) -> None:
        self.data_manager = DummyDataManager(snapshot)
        self.binance_adapter = adapter or DummyBinanceAdapter()
        self.state = None


class TFModelStub:
    def __init__(self, result: str):
        self._result = result

    def predict(self, snapshot):
        return self._result


def patch_tfmodel(monkeypatch, result: str):
    def _factory():
        return TFModelStub(result)

    monkeypatch.setattr(flat_pos_module, "TFModel", lambda: _factory())


class _FakeLongState:
    def __init__(self, parent, target_prices):
        self.parent = parent
        self.target_prices = target_prices


class _FakeShortState:
    def __init__(self, parent, target_prices):
        self.parent = parent
        self.target_prices = target_prices


@pytest.fixture(autouse=True)
def import_stubs(monkeypatch):
    original_import = builtins.__import__

    def import_stub(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "bot.states.active.long_position_state":
            mod = types.ModuleType(name)
            setattr(mod, "LongPositionState", _FakeLongState)
            return mod
        if name == "bot.states.active.short_position_state":
            mod = types.ModuleType(name)
            setattr(mod, "ShortPositionState", _FakeShortState)
            return mod
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_stub)
    yield


def test_is_long_entry_condition_met_true_and_false():
    snap = DummySnapshot(price=90, ema_100=100, macd_12=-0.5, macd_26=-1.0, rsi_6=60)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)
    assert state._is_long_entry_condition_met() is True

    parent.data_manager.is_long_blocked = True
    assert state._is_long_entry_condition_met() is False


def test_is_short_entry_condition_met_true_and_false():
    snap = DummySnapshot(price=110, ema_100=100, macd_12=1.0, macd_26=2.0, rsi_6=40)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)
    assert state._is_short_entry_condition_met() is True

    parent.data_manager.is_short_blocked = True
    assert state._is_short_entry_condition_met() is False


def test_update_position_snapshot_clones():
    snap = DummySnapshot()
    parent = DummyParent(snap)
    state = FlatPositionState(parent)
    state._update_position_snapshot()
    assert parent.data_manager.position_snapshot is not snap
    assert isinstance(parent.data_manager.position_snapshot, DummySnapshot)
    assert parent.data_manager.position_snapshot._cloned is True


def test_apply_long_confirmed_logs_and_state_block_false(monkeypatch):
    snap = DummySnapshot(price=100, ema_100=200, macd_12=-0.5, macd_26=-1.0, rsi_6=60)
    adapter = DummyBinanceAdapter(long_tp=150, long_sl=80)
    parent = DummyParent(snap, adapter=adapter)
    state = FlatPositionState(parent)

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state._apply_long(is_confirmed=True)

    assert adapter.called["enter_long"] == (100, False)
    assert logs and logs[0].startswith("Entered LONG")
    assert "Snapshot(" in logs[1]
    assert parent.data_manager.is_long_blocked is True
    assert isinstance(parent.state, _FakeLongState)


def test_apply_long_not_confirmed_no_logs_and_state_block_true(monkeypatch):
    snap = DummySnapshot(price=123.45)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state._apply_long(is_confirmed=False)

    assert parent.data_manager.is_long_blocked is True
    assert parent.binance_adapter.called["enter_long"] == (123.45, True)
    assert logs == []
    assert isinstance(parent.state, _FakeLongState)


def test_apply_short_confirmed_logs_and_state_block_false(monkeypatch):
    snap = DummySnapshot(price=200, ema_100=100, macd_12=1.5, macd_26=2.0, rsi_6=40)
    adapter = DummyBinanceAdapter(short_tp=180, short_sl=220)
    parent = DummyParent(snap, adapter=adapter)
    state = FlatPositionState(parent)

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state._apply_short(is_confirmed=True)

    assert adapter.called["enter_short"] == (200, False)
    assert logs and logs[0].startswith("Entered SHORT")
    assert "Snapshot(" in logs[1]
    assert parent.data_manager.is_short_blocked is True
    assert isinstance(parent.state, _FakeShortState)


def test_apply_short_not_confirmed_no_logs_and_state_block_true(monkeypatch):
    snap = DummySnapshot(price=201.0)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state._apply_short(is_confirmed=False)

    assert parent.data_manager.is_short_blocked is True
    assert parent.binance_adapter.called["enter_short"] == (201.0, True)
    assert logs == []
    assert isinstance(parent.state, _FakeShortState)


def test_apply_long_path_confirmed_by_tfmodel(monkeypatch):
    snap = DummySnapshot(price=90, ema_100=100, macd_12=-0.5, macd_26=-1.0, rsi_6=60)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    patch_tfmodel(monkeypatch, "LONG")

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state.apply()

    price, state_block = parent.binance_adapter.called["enter_long"]
    assert (price, state_block) == (90, False)
    assert parent.data_manager.is_long_blocked is True
    assert isinstance(parent.state, _FakeLongState)
    assert logs and logs[0].startswith("Entered LONG")


def test_apply_long_path_not_confirmed_by_tfmodel(monkeypatch):
    snap = DummySnapshot(price=95, ema_100=100, macd_12=-0.1, macd_26=-0.5, rsi_6=55)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    patch_tfmodel(monkeypatch, "SHORT")

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state.apply()

    assert parent.binance_adapter.called["enter_long"] == (95, True)
    assert logs == []
    assert isinstance(parent.state, _FakeLongState)


def test_apply_short_path_confirmed_by_tfmodel(monkeypatch):
    snap = DummySnapshot(price=110, ema_100=100, macd_12=1.0, macd_26=2.0, rsi_6=40)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    patch_tfmodel(monkeypatch, "SHORT")

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state.apply()

    price, state_block = parent.binance_adapter.called["enter_short"]
    assert (price, state_block) == (110, False)
    assert parent.data_manager.is_short_blocked is True
    assert isinstance(parent.state, _FakeShortState)
    assert logs and logs[0].startswith("Entered SHORT")


def test_apply_short_path_not_confirmed_by_tfmodel(monkeypatch):
    snap = DummySnapshot(price=130, ema_100=100, macd_12=0.5, macd_26=1.0, rsi_6=40)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    patch_tfmodel(monkeypatch, "LONG")

    logs: list[str] = []
    monkeypatch.setattr(
        flat_pos_module.Logger, "log_info", lambda msg: logs.append(msg)
    )

    state.apply()

    assert parent.binance_adapter.called["enter_short"] == (130, True)
    assert logs == []
    assert isinstance(parent.state, _FakeShortState)


def test_apply_no_branch_when_conditions_false(monkeypatch):
    snap = DummySnapshot(price=100, ema_100=100, macd_12=0.0, macd_26=0.0, rsi_6=50)
    parent = DummyParent(snap)
    state = FlatPositionState(parent)

    patch_tfmodel(monkeypatch, "LONG")

    state.apply()
    assert parent.state is None
    assert "enter_long" not in parent.binance_adapter.called
    assert "enter_short" not in parent.binance_adapter.called
