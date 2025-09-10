import types
from datetime import datetime as RealDateTime
from utils.date_utils import DateUtils
import utils.date_utils as date_utils_module


def test_get_date_returns_expected_format(monkeypatch):
    class FixedDateTime(RealDateTime):
        @classmethod
        def now(cls, tz=None):
            return cls(2023, 1, 2, 3, 4, 5)

    monkeypatch.setattr(
        date_utils_module,
        "datetime",
        types.SimpleNamespace(datetime=FixedDateTime),
    )

    result = DateUtils.get_date()
    assert isinstance(result, str)
    assert result == "[2023-01-02 03:04:05]"
