# import pytest
# from typing import TypedDict, cast, Dict, Any

# from bot.bot_settings import SETTINGS, BotSettings


# class BotArgs(TypedDict, total=False):
#     API_PUBLIC_KEY: str
#     API_SECRET_KEY: str
#     SYMBOL: str
#     COIN_PRECISION: int
#     TP_RATIO: float
#     SL_RATIO: float
#     LEVERAGE: int
#     TEST_MODE: bool
#     INTERVAL: str
#     SLEEP_DURATION: float
#     OUTPUT_CSV_PATH: str


# def test_module_level_settings_is_initialized_and_valid():
#     settings_instance = SETTINGS
#     assert isinstance(settings_instance, BotSettings)
#     assert (
#         isinstance(settings_instance.SYMBOL, str) and settings_instance.SYMBOL.strip()
#     )
#     assert settings_instance.SLEEP_DURATION > 0


# def test_from_toml_returns_instance_and_valid_fields():
#     settings_from_file = BotSettings.from_toml("settings.toml")
#     assert isinstance(settings_from_file, BotSettings)
#     assert settings_from_file.LEVERAGE >= 1
#     assert settings_from_file.TP_RATIO > 0
#     assert settings_from_file.SL_RATIO > 0
#     assert (
#         isinstance(settings_from_file.INTERVAL, str)
#         and settings_from_file.INTERVAL.strip()
#     )


# def test_from_mapping_happy_path_and_type_conversions():
#     mapping: Dict[str, Any] = {
#         "api": {"public_key": 12345, "secret_key": 67890},
#         "position": {
#             "symbol": "BTCUSDT",
#             "coin_precision": "4",
#             "tp_ratio": "0.01",
#             "sl_ratio": 0.02,
#             "leverage": "5",
#         },
#         "runtime": {"test_mode": False, "interval": "1h", "sleep_duration": "3.5"},
#         "output": {"csv_path": "/tmp/out.csv"},
#     }
#     settings_instance = BotSettings.from_mapping(mapping)
#     assert settings_instance.API_PUBLIC_KEY == "12345"
#     assert settings_instance.API_SECRET_KEY == "67890"
#     assert settings_instance.SYMBOL == "BTCUSDT"
#     assert settings_instance.COIN_PRECISION == 4
#     assert settings_instance.TP_RATIO == 0.01
#     assert settings_instance.SL_RATIO == 0.02
#     assert settings_instance.LEVERAGE == 5
#     assert settings_instance.TEST_MODE is False
#     assert settings_instance.INTERVAL == "1h"
#     assert settings_instance.SLEEP_DURATION == 3.5
#     assert settings_instance.OUTPUT_CSV_PATH == "/tmp/out.csv"


# def test_from_mapping_rejects_non_bool_test_mode():
#     with pytest.raises(TypeError, match="test_mode must be a boolean"):
#         BotSettings.from_mapping({"runtime": {"test_mode": "yes"}})


# @pytest.mark.parametrize(
#     "bad_kwargs, expected_message",
#     [
#         ({"SYMBOL": ""}, "SYMBOL cannot be empty"),
#         ({"COIN_PRECISION": -1}, "COIN_PRECISION cannot be negative"),
#         ({"LEVERAGE": 0}, "LEVERAGE must be at least 1"),
#         ({"TP_RATIO": 0}, "TP_RATIO must be greater than 0"),
#         ({"SL_RATIO": 0}, "SL_RATIO must be greater than 0"),
#         ({"INTERVAL": "15"}, "Invalid INTERVAL"),
#         ({"SLEEP_DURATION": 0}, "SLEEP_DURATION must be greater than 0"),
#         (
#             {"TEST_MODE": False, "API_PUBLIC_KEY": "", "API_SECRET_KEY": ""},
#             "API keys must not be empty",
#         ),
#         ({"OUTPUT_CSV_PATH": "   "}, "OUTPUT_CSV_PATH cannot be empty"),
#     ],
# )
# def test_validation_errors_individually(
#     bad_kwargs: Dict[str, Any], expected_message: str
# ):
#     base_args: BotArgs = {
#         "API_PUBLIC_KEY": "pk",
#         "API_SECRET_KEY": "sk",
#         "SYMBOL": "ETHUSDT",
#         "COIN_PRECISION": 2,
#         "TP_RATIO": 0.005,
#         "SL_RATIO": 0.005,
#         "LEVERAGE": 1,
#         "TEST_MODE": True,
#         "INTERVAL": "15m",
#         "SLEEP_DURATION": 1.0,
#         "OUTPUT_CSV_PATH": "./out.csv",
#     }
#     merged: Dict[str, Any] = {**base_args, **bad_kwargs}
#     with pytest.raises(ValueError, match=expected_message):
#         BotSettings(**cast(BotArgs, merged))


# @pytest.mark.parametrize("valid_interval", ["30s", "15m", "1h", "4h", "1d", "2w"])
# def test_interval_accepts_valid_values(valid_interval: str):
#     settings_instance = BotSettings(
#         API_PUBLIC_KEY="pk",
#         API_SECRET_KEY="sk",
#         SYMBOL="X",
#         INTERVAL=valid_interval,
#     )
#     assert settings_instance.INTERVAL == valid_interval


# @pytest.mark.parametrize("invalid_interval", ["", "1", "h1", "1mo", " 15m", "1M"])
# def test_interval_rejects_invalid_values(invalid_interval: str):
#     with pytest.raises(ValueError, match="Invalid INTERVAL"):
#         BotSettings(
#             API_PUBLIC_KEY="pk",
#             API_SECRET_KEY="sk",
#             SYMBOL="X",
#             INTERVAL=invalid_interval,
#         )


# def test_test_mode_false_requires_api_keys():
#     with pytest.raises(ValueError, match="API keys must not be empty"):
#         BotSettings(API_PUBLIC_KEY="", API_SECRET_KEY="", SYMBOL="X", TEST_MODE=False)
