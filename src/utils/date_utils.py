import datetime


class DateUtils:
    """
    Utility class for working with dates and times.

    Provides helper methods to format and retrieve
    the current date and time in standardized formats.
    """

    @staticmethod
    def get_date() -> str:
        """
        Get the current date and time as a formatted string.

        Returns:
            str: Current timestamp in the format "[YYYY-MM-DD HH:MM:SS]".
        """
        return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
