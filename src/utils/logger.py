from termcolor import colored
from utils.date_utils import DateUtils
from colorama import init

init(autoreset=True)


class Logger:
    """
    Console logger with colored output.

    Provides class-level methods for logging different message types
    such as success, failure, info, exception, and startup events.
    """

    @classmethod
    def _log(cls, color: str, message: str) -> None:
        """
        Print a message to the console with a timestamp and color.

        Args:
            color (str): The color name supported by termcolor.
            message (str): The log message to be displayed.
        """
        print(f"{DateUtils.get_date()} {colored(message, color)}")

    @classmethod
    def log_success(cls, message: str) -> None:
        """
        Log a success message in green.

        Args:
            message (str): The success message to log.
        """
        cls._log("green", message)

    @classmethod
    def log_failure(cls, message: str) -> None:
        """
        Log a failure message in dark red (if supported) or red.

        Args:
            message (str): The failure message to log.
        """
        cls._log(
            "dark_red" if "dark_red" in colored.__code__.co_consts else "red", message
        )

    @classmethod
    def log_info(cls, message: str) -> None:
        """
        Log an informational message in yellow.

        Args:
            message (str): The informational message to log.
        """
        cls._log("yellow", message)

    @classmethod
    def log_exception(cls, message: str) -> None:
        """
        Log an exception message in red.

        Args:
            message (str): The exception message to log.
        """
        cls._log("red", message)

    @classmethod
    def log_start(cls, message: str) -> None:
        """
        Log a startup message in cyan.

        Args:
            message (str): The startup message to log.
        """
        cls._log("cyan", message)
