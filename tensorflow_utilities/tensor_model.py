import tensorflow as tf
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, BatchNormalization, LeakyReLU
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import numpy as np

class TensorModel:
    def __init__(self, file_path):
        
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("No data in csv file")

        self.columns = ["price", "macd_12", "macd_26", "ema_100", "rsi_6"]
        
        self.X = df[self.columns].values
        y = df['state'].values
        self.y = np.where(y == 'LONG', 1, 0)

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.1, random_state=42)

        self.model = Sequential([
            # add your layers here
            Dense(1, activation='sigmoid')
        ])

        optimizer = Adam(learning_rate=0.01)
        self.model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])  # Binary crossentropy
        self.model.fit(self.X_train, self.y_train, epochs=32, batch_size=1, validation_split=0.2, verbose=0)
    
    def getAccuracy(self):
        _, test_acc = self.model.evaluate(self.X_test, self.y_test, verbose=0)
        return test_acc
    
    def predictResult(self, data_obj):
        features = [float(data_obj.price),
                    float(data_obj.macd_12), float(data_obj.macd_26),
                    float(data_obj.ema_100), float(data_obj.rsi_6)]

        new_data = np.array([features])

        prediction_prob = self.model.predict(new_data, verbose=0)[0][0]  # Tek çıktı olduğu için [0][0]
        prediction = "LONG" if prediction_prob >= 0.5 else "SHORT"  # Olasılık eşik değeri 0.5

        return prediction
    
    def process_model(self, data_obj):
        accuracy = self.getAccuracy()
        prediction = self.predictResult(data_obj)
        return accuracy, prediction
