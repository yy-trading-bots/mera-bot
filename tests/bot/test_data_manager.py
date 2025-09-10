from bot.data_manager import DataManager
import bot.data_manager as data_manager_module


def test_initial_state_has_expected_flags_and_no_snapshots():
    manager = DataManager()
    assert manager.is_long_blocked is False
    assert manager.is_short_blocked is False
    assert not hasattr(manager, "market_snapshot")
    assert not hasattr(manager, "position_snapshot")


def test_block_short_sets_flags_and_logs_in_order(monkeypatch):
    log_messages = []

    def fake_log_info(message: str) -> None:
        log_messages.append(message)

    monkeypatch.setattr(data_manager_module.Logger, "log_info", fake_log_info)

    manager = DataManager()
    manager.block_short()

    assert manager.is_short_blocked is True
    assert manager.is_long_blocked is False
    assert log_messages == [
        "SHORT trading is BLOCKED.",
        "LONG trading is UNBLOCKED.",
    ]


def test_block_long_sets_flags_and_logs_in_order(monkeypatch):
    log_messages = []

    def fake_log_info(message: str) -> None:
        log_messages.append(message)

    monkeypatch.setattr(data_manager_module.Logger, "log_info", fake_log_info)

    manager = DataManager()
    manager.block_long()

    assert manager.is_long_blocked is True
    assert manager.is_short_blocked is False
    assert log_messages == [
        "Long trading is BLOCKED.",
        "Short trading is UNBLOCKED.",
    ]
