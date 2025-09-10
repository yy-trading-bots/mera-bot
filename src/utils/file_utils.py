import csv
from pathlib import Path
from typing import Union, Iterable, Any, Dict
from data.market_snapshot import MarketSnapshot
import tomllib


class FileUtils:
    """
    Utility class for file operations including:
        - Ensuring directory paths
        - Writing results to CSV
        - Reading configuration from TOML files
    """

    _HEADER = [
        "date",
        "result",
        "position",
        "price",
        "macd_12",
        "macd_26",
        "ema_100",
        "rsi_6",
    ]

    @staticmethod
    def _ensure_parent(path: Union[str, Path]) -> None:
        """
        Ensure that the parent directory of the given path exists.

        Args:
            path (Union[str, Path]): File path for which to ensure parent directory.
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _is_empty_file(path: Union[str, Path]) -> bool:
        """
        Check whether the file at the given path exists and is non-empty.

        Args:
            path (Union[str, Path]): File path to check.

        Returns:
            bool: True if the file does not exist or is empty, False otherwise.
        """
        p = Path(path)
        return (not p.exists()) or (p.stat().st_size == 0)

    @staticmethod
    def _append_csv(path: Union[str, Path], row: Iterable[Union[str, float]]) -> None:
        """
        Append a row of data to a CSV file. If the file is new or empty,
        a header row is written first.

        Args:
            path (Union[str, Path]): Path to the CSV file.
            row (Iterable[Union[str, float]]): Row data to append.
        """
        FileUtils._ensure_parent(path)
        write_header = FileUtils._is_empty_file(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(FileUtils._HEADER)
            writer.writerow(row)

    @staticmethod
    def save_result(
        file_path: Union[str, Path],
        result: str,
        position: str,
        snapshot: MarketSnapshot,
    ) -> None:
        """
        Save a trading result into a CSV file.

        Args:
            file_path (Union[str, Path]): Path to the results CSV file.
            result (str): Outcome of the trade ("WIN"/"LOSS" or similar).
            position (str): Position side ("LONG"/"SHORT").
            snapshot (MarketSnapshot): Market snapshot at the time of entry/exit.
        """
        row = [
            snapshot.date,
            result,
            position,
            float(snapshot.price),
            float(snapshot.macd_12),
            float(snapshot.macd_26),
            float(snapshot.ema_100),
            float(snapshot.rsi_6),
        ]
        FileUtils._append_csv(file_path, row)

    @staticmethod
    def read_toml_file(path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a TOML configuration file.

        Args:
            path (Union[str, Path]): Path to the TOML file.

        Returns:
            Dict[str, Any]: Parsed TOML content as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If parsing fails or the content is not a dictionary.
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"TOML file not found: {p}")

        with p.open("rb") as f:
            try:
                data = tomllib.load(f)
            except Exception as exc:
                raise ValueError(f"Failed to parse TOML file: {p}") from exc

        if not isinstance(data, dict):
            raise ValueError("Top-level TOML content must be a table/object.")

        return data
