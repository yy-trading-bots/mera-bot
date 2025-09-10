import pytest
from bot.mera_bot import MeraBot
import bot.mera_bot as mera_bot_module


class Snapshot:
    def __init__(self, price: float, ema_100: float) -> None:
        self.price = price
        self.ema_100 = ema_100


class FakeIndicatorManager:
    def __init__(self, snapshot: Snapshot) -> None:
        self._snapshot = snapshot

    def fetch_indicators(self) -> Snapshot:
        return self._snapshot


class FakeBinanceAdapter:
    def __init__(self, snapshot: Snapshot) -> None:
        self.indicator_manager = FakeIndicatorManager(snapshot)


class FakeState(mera_bot_module.PositionState):
    def __init__(self, parent: MeraBot) -> None:
        super().__init__(parent=parent)

    # PositionState.step is final; implement only apply()
    def apply(self) -> None:
        # No-op here; we don't rely on this to break the loop anymore.
        return None


def test_init_blocks_long_when_price_below_ema(monkeypatch):
    start_logs = []

    def fake_log_start(message: str) -> None:
        start_logs.append(message)

    monkeypatch.setattr(mera_bot_module.Logger, "log_start", fake_log_start)
    monkeypatch.setattr(mera_bot_module, "FlatPositionState", FakeState)

    snapshot = Snapshot(price=100.0, ema_100=150.0)

    def adapter_factory(*_args, **_kwargs):
        return FakeBinanceAdapter(snapshot)

    monkeypatch.setattr(mera_bot_module, "BinanceAdapter", adapter_factory)

    bot = MeraBot()

    assert bot.data_manager.is_long_blocked is True
    assert bot.data_manager.is_short_blocked is False
    assert isinstance(bot.state, FakeState)
    assert bot.state.parent is bot
    assert start_logs == ["MeraBot is running..."]


def test_init_blocks_short_when_price_at_or_above_ema(monkeypatch):
    monkeypatch.setattr(mera_bot_module, "FlatPositionState", FakeState)

    snapshot = Snapshot(price=200.0, ema_100=150.0)

    def adapter_factory(*_args, **_kwargs):
        return FakeBinanceAdapter(snapshot)

    monkeypatch.setattr(mera_bot_module, "BinanceAdapter", adapter_factory)

    bot = MeraBot()

    assert bot.data_manager.is_short_blocked is True
    assert bot.data_manager.is_long_blocked is False
    assert isinstance(bot.state, FakeState)
    assert bot.state.parent is bot


def test_run_exits_when_sleep_raises_and_sleep_called_once(monkeypatch):
    # Force the loop to exit deterministically by raising from sleep.
    calls = []

    class StopLoop(Exception):
        pass

    def fake_sleep(seconds: float) -> None:
        calls.append(seconds)
        raise StopLoop

    monkeypatch.setattr(mera_bot_module, "sleep", fake_sleep)
    monkeypatch.setattr(mera_bot_module, "FlatPositionState", FakeState)

    snapshot = Snapshot(price=100.0, ema_100=50.0)

    def adapter_factory(*_args, **_kwargs):
        return FakeBinanceAdapter(snapshot)

    monkeypatch.setattr(mera_bot_module, "BinanceAdapter", adapter_factory)

    bot = MeraBot()

    with pytest.raises(StopLoop):
        bot.run()

    assert len(calls) == 1
    assert isinstance(calls[0], (int, float))
