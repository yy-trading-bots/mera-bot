import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import Model
from tensorflow.keras.models import Sequential
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
from bot.bot_settings import SETTINGS


class TFModel:
    """
    TensorFlow-based binary classification model for predicting trading positions.

    The model uses a simple feedforward neural network with a sigmoid activation
    to classify whether the state is "LONG" or "SHORT" based on market indicators.
    """

    def __init__(self):
        """
        Initialize the TFModel instance.

        Steps:
            - Load data from the configured CSV path.
            - Validate that the dataset is not empty.
            - Prepare training and testing data.
            - Train the neural network model.

        Raises:
            ValueError: If the CSV file contains no data.
        """
        df = pd.read_csv(SETTINGS.OUTPUT_CSV_PATH)
        if df.empty:
            raise ValueError("No data in csv file")

        self.columns = ["price", "macd_12", "macd_26", "ema_100", "rsi_6"]
        X_train, X_test, y_train, y_test = self._prepare_data(df)
        self.X_train, self.X_test = X_train, X_test
        self.y_train, self.y_test = y_train, y_test

        self.model = self._train_model()

    def _prepare_data(self, df: pd.DataFrame):
        """
        Prepare the dataset for training and testing.

        Args:
            df (pd.DataFrame): Input DataFrame containing features and target state.

        Returns:
            tuple: X_train, X_test, y_train, y_test
        """
        X = df[self.columns].values
        y = np.where(df["result"].values == "LONG", 1, 0).astype(np.float32)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.1, random_state=42, stratify=y
        )
        return X_train, X_test, y_train, y_test

    def _build_model(self, input_dim: int) -> Model:
        """
        Build the Keras Sequential model architecture.

        Args:
            input_dim (int): Number of input features.

        Returns:
            Model: Compiled Keras model ready for training.
        """
        model = Sequential(
            [
                # add your model layers here
                #
                #
                #
                Dense(1, activation="sigmoid", input_shape=(input_dim,))
            ]
        )
        optimizer = Adam(learning_rate=0.01)
        model.compile(
            optimizer=optimizer, loss="binary_crossentropy", metrics=["accuracy"]
        )
        return model

    def _train_model(
        self,
        epochs: int = 32,
        batch_size: int = 1,
        validation_split: float = 0.2,
        verbose: int = 0,
    ) -> Model:
        """
        Train the model on the prepared training data.

        Args:
            epochs (int, optional): Number of training epochs. Defaults to 32.
            batch_size (int, optional): Batch size for training. Defaults to 1.
            validation_split (float, optional): Fraction of training data for validation. Defaults to 0.2.
            verbose (int, optional): Verbosity mode. Defaults to 0.

        Returns:
            Model: Trained Keras model.
        """
        model = self._build_model(input_dim=len(self.columns))
        model.fit(
            self.X_train,
            self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose,
        )
        return model

    def get_accuracy_metric(self) -> float:
        """
        Evaluate the trained model on the test set.

        Returns:
            float: Accuracy score on the test dataset.
        """
        _, test_acc = self.model.evaluate(self.X_test, self.y_test, verbose=0)
        return test_acc

    def predict(self, indicators) -> str:
        """
        Predict the trading state ("LONG" or "SHORT") given new market indicators.

        Args:
            indicators: An object containing market indicator attributes.

        Returns:
            str: Predicted state ("LONG" if probability >= 0.5, else "SHORT").
        """
        features = [
            float(indicators.price),
            float(indicators.macd_12),
            float(indicators.macd_26),
            float(indicators.ema_100),
            float(indicators.rsi_6),
        ]
        new_data = np.array([features])
        prob = self.model.predict(new_data, verbose=0)[0][0]
        return "LONG" if prob >= 0.5 else "SHORT"
