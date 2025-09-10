from bot.performance_tracker import PerformanceTracker


def test_initial_state():
    tracker = PerformanceTracker()
    assert tracker.win_count == 0
    assert tracker.loss_count == 0


def test_calculate_win_rate_when_no_trades():
    tracker = PerformanceTracker()
    assert tracker.calculate_win_rate() == "0.00%"


def test_increase_win_with_default_and_custom_values():
    tracker = PerformanceTracker()
    tracker.increase_win()  # +1
    tracker.increase_win(3)  # +3
    assert tracker.win_count == 4
    assert tracker.loss_count == 0


def test_increase_loss_with_default_and_custom_values():
    tracker = PerformanceTracker()
    tracker.increase_loss()  # +1
    tracker.increase_loss(2)  # +2
    assert tracker.win_count == 0
    assert tracker.loss_count == 3


def test_calculate_win_rate_general_case_rounds_to_two_decimals():
    tracker = PerformanceTracker()
    tracker.increase_win(1)
    tracker.increase_loss(2)  # total = 3, win rate = 33.33%
    assert tracker.calculate_win_rate() == "33.33%"


def test_calculate_win_rate_single_decimal_representation():
    tracker = PerformanceTracker()
    tracker.increase_win(1)
    tracker.increase_loss(3)  # total = 4, win rate = 25.0% -> "25.0%"
    assert tracker.calculate_win_rate() == "25.0%"
