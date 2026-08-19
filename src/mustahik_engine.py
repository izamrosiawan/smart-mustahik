import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class SmartMustahikClassifier:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = RandomForestClassifier(n_estimators=100, random_state=random_state)
        self.features = ['hdi', 'sanitation_access_percent', 'drinking_water_access_percent', 
                         'school_participation_rate', 'unemployment_rate', 'population_density']

    def train(self, X: pd.DataFrame, y: pd.Series):
        self.model.fit(X[self.features], y)
        return self

    def predict_priority(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X[self.features])
