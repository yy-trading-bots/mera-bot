import pytest
from utils.logger import Logger
import utils.logger as logger_module
from utils.date_utils import DateUtils


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setattr(
        DateUtils, "get_date", staticmethod(lambda: "[2023-01-02 03:04:05]")
    )


def _set_colored_stub(monkeypatch, include_dark_red: bool):
    if include_dark_red:

        def colored(msg, color):
            _ = "dark_red"  # ensure literal is in co_consts
            return f"<{color}>{msg}"

    else:

        def colored(msg, color):
            return f"<{color}>{msg}"

    monkeypatch.setattr(logger_module, "colored", colored)


def test_log_success_info_exception_start_use_expected_colors(capsys, monkeypatch):
    _set_colored_stub(monkeypatch, include_dark_red=False)

    Logger.log_success("ok")
    Logger.log_info("info")
    Logger.log_exception("boom")
    Logger.log_start("go")

    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "[2023-01-02 03:04:05] <green>ok"
    assert out[1] == "[2023-01-02 03:04:05] <yellow>info"
    assert out[2] == "[2023-01-02 03:04:05] <red>boom"
    assert out[3] == "[2023-01-02 03:04:05] <cyan>go"


def test_log_failure_uses_dark_red_when_available(capsys, monkeypatch):
    _set_colored_stub(monkeypatch, include_dark_red=True)

    Logger.log_failure("bad")
    out = capsys.readouterr().out.strip()
    assert out == "[2023-01-02 03:04:05] <dark_red>bad"


def test_log_failure_falls_back_to_red_when_dark_red_absent(capsys, monkeypatch):
    _set_colored_stub(monkeypatch, include_dark_red=False)

    Logger.log_failure("bad")
    out = capsys.readouterr().out.strip()
    assert out == "[2023-01-02 03:04:05] <red>bad"


def test__log_direct_call(capsys, monkeypatch):
    _set_colored_stub(monkeypatch, include_dark_red=False)

    Logger._log("magenta", "direct")
    out = capsys.readouterr().out.strip()
    assert out == "[2023-01-02 03:04:05] <magenta>direct"
