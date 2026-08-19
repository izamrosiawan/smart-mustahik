import pytest
import pandas as pd
import numpy as np
from src.mustahik_engine import SmartMustahikClassifier

def test_mustahik_engine():
    X = pd.DataFrame({
        'hdi': [65.0, 72.0, 80.0, 60.0],
        'sanitation_access_percent': [70.0, 85.0, 95.0, 50.0],
        'drinking_water_access_percent': [75.0, 90.0, 98.0, 60.0],
        'school_participation_rate': [80.0, 90.0, 98.0, 70.0],
        'unemployment_rate': [6.5, 4.2, 3.1, 8.5],
        'population_density': [1200, 2500, 5000, 800]
    })
    y = pd.Series([1, 0, 0, 1])
    
    engine = SmartMustahikClassifier()
    engine.train(X, y)
    preds = engine.predict_priority(X)
    
    assert len(preds) == 4
    assert np.all(np.isin(preds, [0, 1]))
