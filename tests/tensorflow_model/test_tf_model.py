import importlib
import numpy as np
import pandas as pd
import pytest
from typing import Optional

tf_model_module = importlib.import_module("tensorflow_model.tf_model")
TFModel = tf_model_module.TFModel


class _FakeKerasModel:
    def __init__(self):
        self._compiled = False
        self.compile_args = {}
        self.fit_args = {}
        self._eval_return = (0.0, 0.88)
        self._predict_values: Optional[np.ndarray] = None

    def compile(self, optimizer=None, loss=None, metrics=None):
        self._compiled = True
        self.compile_args = {"optimizer": optimizer, "loss": loss, "metrics": metrics}

    def fit(self, x, y, epochs, batch_size, validation_split, verbose):
        self.fit_args = {
            "epochs": epochs,
            "batch_size": batch_size,
            "validation_split": validation_split,
            "verbose": verbose,
            "x_shape": np.shape(x),
            "y_shape": np.shape(y),
        }

    def evaluate(self, x, y, verbose=0):
        return self._eval_return

    def predict(self, x, verbose=0):
        if self._predict_values is not None:
            return self._predict_values
        return np.array([[0.6]], dtype=np.float32)


class _FakeAdam:
    def __init__(self, learning_rate):
        self.learning_rate = learning_rate


def _fake_Dense(*args, **kwargs):
    return ("Dense", args, tuple(sorted(kwargs.items())))


def _fake_Sequential(layers):
    return _FakeKerasModel()


def _make_df(n_rows: int = 20) -> pd.DataFrame:
    results = ["LONG", "SHORT"] * (n_rows // 2)
    if len(results) < n_rows:
        results.append("LONG")
    return pd.DataFrame(
        {
            "result": results[:n_rows],
            "price": np.linspace(90.0, 110.0, n_rows),
            "macd_12": np.linspace(-1.0, 1.0, n_rows),
            "macd_26": np.linspace(-0.5, 0.5, n_rows),
            "ema_100": np.linspace(95.0, 105.0, n_rows),
            "rsi_6": np.linspace(30.0, 70.0, n_rows),
        }
    )


def _apply_fakes(monkeypatch):
    monkeypatch.setattr(tf_model_module, "Dense", _fake_Dense, raising=False)
    monkeypatch.setattr(tf_model_module, "Sequential", _fake_Sequential, raising=False)
    monkeypatch.setattr(tf_model_module, "Adam", _FakeAdam, raising=False)


def test_init_trains_and_sets_fields(monkeypatch):
    _apply_fakes(monkeypatch)
    df = _make_df(20)
    monkeypatch.setattr(tf_model_module.pd, "read_csv", lambda path: df)
    model = TFModel()
    assert model.columns == ["price", "macd_12", "macd_26", "ema_100", "rsi_6"]
    assert model.X_train.shape[1] == 5
    assert model.y_train.ndim == 1
    assert isinstance(model.model, _FakeKerasModel)
    assert model.model._compiled is True
    assert isinstance(model.model.compile_args["optimizer"], _FakeAdam)
    assert model.model.compile_args["optimizer"].learning_rate == 0.01
    assert model.model.compile_args["loss"] == "binary_crossentropy"
    assert model.model.compile_args["metrics"] == ["accuracy"]
    assert model.model.fit_args["epochs"] == 32
    assert model.model.fit_args["batch_size"] == 1
    assert model.model.fit_args["validation_split"] == 0.2
    assert model.model.fit_args["verbose"] == 0


def test_init_raises_on_empty_csv(monkeypatch):
    _apply_fakes(monkeypatch)
    empty_df = pd.DataFrame()
    monkeypatch.setattr(tf_model_module.pd, "read_csv", lambda path: empty_df)
    with pytest.raises(ValueError, match="No data in csv file"):
        TFModel()


def test_build_model_compiles_with_expected_params(monkeypatch):
    _apply_fakes(monkeypatch)
    df = _make_df(20)
    monkeypatch.setattr(tf_model_module.pd, "read_csv", lambda path: df)
    m = TFModel()
    built = m._build_model(input_dim=5)
    assert isinstance(built, _FakeKerasModel)
    assert built._compiled is True
    assert isinstance(built.compile_args["optimizer"], _FakeAdam)
    assert built.compile_args["loss"] == "binary_crossentropy"
    assert built.compile_args["metrics"] == ["accuracy"]


def test_get_accuracy_metric(monkeypatch):
    _apply_fakes(monkeypatch)
    df = _make_df(20)
    monkeypatch.setattr(tf_model_module.pd, "read_csv", lambda path: df)
    m = TFModel()
    acc = m.get_accuracy_metric()
    assert 0.87 < acc < 0.89


def test_predict_long_and_short(monkeypatch):
    _apply_fakes(monkeypatch)
    df = _make_df(20)
    monkeypatch.setattr(tf_model_module.pd, "read_csv", lambda path: df)
    m = TFModel()

    class Indicators:
        def __init__(self, price, macd_12, macd_26, ema_100, rsi_6):
            self.price = price
            self.macd_12 = macd_12
            self.macd_26 = macd_26
            self.ema_100 = ema_100
            self.rsi_6 = rsi_6

    ind = Indicators(100, 0.1, -0.1, 102, 55)

    fake_long_model = _FakeKerasModel()
    fake_long_model._predict_values = np.array([[0.75]], dtype=np.float32)
    m.model = fake_long_model
    assert m.predict(ind) == "LONG"

    fake_short_model = _FakeKerasModel()
    fake_short_model._predict_values = np.array([[0.25]], dtype=np.float32)
    m.model = fake_short_model
    assert m.predict(ind) == "SHORT"
