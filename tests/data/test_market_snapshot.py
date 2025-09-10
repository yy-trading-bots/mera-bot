from data.market_snapshot import MarketSnapshot


def test_init_converts_numbers():
    src_bars = [(10.0, 11.0, 9.0, 12.0), (20.5, 21.5, 19.0, 22.0)]
    snap = MarketSnapshot(
        date="2025-08-29 00:00",
        price=100,  # int -> float
        macd_12=1,  # int -> float
        macd_26=-2,  # int -> float
        ema_100=200,  # int -> float
        rsi_6=50,  # int -> float
    )

    assert isinstance(snap.price, float) and snap.price == 100.0
    assert isinstance(snap.macd_12, float) and snap.macd_12 == 1.0
    assert isinstance(snap.macd_26, float) and snap.macd_26 == -2.0
    assert isinstance(snap.ema_100, float) and snap.ema_100 == 200.0
    assert isinstance(snap.rsi_6, float) and snap.rsi_6 == 50.0


def test_str_formatting_two_decimals():
    snap = MarketSnapshot(
        date="2025-08-29 00:00",
        price=123.456,
        macd_12=1.234,
        macd_26=-4.567,
        ema_100=200.0,
        rsi_6=49.5,
    )
    expected = "PRICE: 123.46 | MACD_12: 1.23 | MACD_26: -4.57 | EMA_100: 200.00 | RSI_6: 49.50"
    assert str(snap) == expected


def test_clone_returns_deep_copy_and_is_independent():
    original = MarketSnapshot(
        date="2025-08-29 00:00",
        price=10.0,
        macd_12=0.1,
        macd_26=0.2,
        ema_100=100.0,
        rsi_6=55.0,
    )

    cloned = original.clone()

    assert cloned is not original
    assert cloned.date == original.date
    assert cloned.price == original.price
    assert cloned.macd_12 == original.macd_12
    assert cloned.macd_26 == original.macd_26
    assert cloned.ema_100 == original.ema_100
    assert cloned.rsi_6 == original.rsi_6
