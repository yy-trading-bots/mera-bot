class PerformanceTracker:
    """
    Tracks trading performance by maintaining win and loss counts.

    Provides utilities to increment results and calculate the overall
    win rate as a percentage string.
    """

    def __init__(self) -> None:
        """
        Initialize the PerformanceTracker with zero wins and losses.

        Attributes:
            win_count (int): Total number of winning trades.
            loss_count (int): Total number of losing trades.
        """
        self.win_count: int = 0
        self.loss_count: int = 0

    def calculate_win_rate(self) -> str:
        """
        Calculate the win rate as a percentage string.

        Returns:
            str: The win rate in the format "xx.xx%".
                 If no trades have been recorded, returns "0.00%".
        """
        total: int = self.win_count + self.loss_count
        if total == 0:
            return "0.00%"
        win_rate: float = self.win_count / total
        win_rate_percentage: float = round(win_rate * 100, 2)
        return f"{win_rate_percentage}%"

    def increase_win(self, n: int = 1) -> None:
        """
        Increment the win count.

        Args:
            n (int, optional): Number of wins to add. Defaults to 1.
        """
        self.win_count += n

    def increase_loss(self, n: int = 1) -> None:
        """
        Increment the loss count.

        Args:
            n (int, optional): Number of losses to add. Defaults to 1.
        """
        self.loss_count += n
