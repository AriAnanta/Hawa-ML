import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="AQI Prediction API",
    description="API untuk prediksi AQI (ISPU) 48 jam ke depan",
    version="1.0.0"
)

# Load model
PIPELINE_PATH = Path(__file__).resolve().parent.parent / "aqi_pipeline_enhanced.pkl"
pipeline_data = joblib.load(PIPELINE_PATH)
model = pipeline_data["model"]
FEATURES = pipeline_data["features"]
LAGS = pipeline_data["lags"]
ROLLS = pipeline_data["rolls"]
MAX_LOOKBACK = max(max(LAGS), max(ROLLS)) + 1

# AQI interpolation points (PM2.5 -> ISPU)
X_POINTS = np.array([0.0, 15.5, 55.4, 150.4, 250.4, 500.0])
Y_POINTS = np.array([0, 50, 100, 200, 300, 500])


class HistoryItem(BaseModel):
    timestamp: datetime
    pm25_density: float
    aqi_ispu: Optional[float] = None


def preprocess_history(items: List[HistoryItem]) -> pd.DataFrame:
    df = pd.DataFrame([i.model_dump() for i in items])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").set_index("timestamp")
    df = df[["pm25_density"]].copy()
    
    # Hitung AQI dari PM2.5
    df["aqi_ispu"] = np.interp(df["pm25_density"], X_POINTS, Y_POINTS)
    df = df.resample("1h").mean().ffill()
    
    if len(df) < MAX_LOOKBACK:
        raise HTTPException(status_code=400, detail=f"Butuh minimal {MAX_LOOKBACK} data")
    
    return df.tail(MAX_LOOKBACK)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month
    df["weekofyear"] = df.index.isocalendar().week.astype(int)
    df["dayofyear"] = df.index.dayofyear
    
    for l in LAGS:
        df[f"aqi_lag_{l}"] = df["aqi_ispu"].shift(l)
        df[f"pm25_lag_{l}"] = df["pm25_density"].shift(l)
    
    for r in ROLLS:
        df[f"aqi_roll_mean_{r}"] = df["aqi_ispu"].rolling(r).mean()
        df[f"aqi_roll_std_{r}"] = df["aqi_ispu"].rolling(r).std()
    
    return df


def forecast_48h(history: pd.DataFrame) -> list:
    current = history.copy()
    results = []
    last_timestamp = current.index[-1]
    
    for i in range(1, 49):
        next_time = last_timestamp + timedelta(hours=i)
        next_row = pd.DataFrame(index=[next_time], columns=current.columns, dtype=float)
        next_row["pm25_density"] = current["pm25_density"].iloc[-1]
        next_row["aqi_ispu"] = np.nan
        temp = pd.concat([current, next_row])
        
        df_feat = add_features(temp).dropna()
        X_next = df_feat.iloc[[-1]][FEATURES]
        pred_aqi = float(model.predict(X_next)[0])
        
        results.append({
            "timestamp": next_time.isoformat(),
            "predicted_aqi": round(pred_aqi, 2)
        })
        
        temp.loc[next_time, "aqi_ispu"] = pred_aqi
        current = temp
    
    return results


@app.post("/predict")
def predict(history: List[HistoryItem]):
    """
    Prediksi AQI untuk 48 jam ke depan
    
    Butuh minimal 49 data historis per jam:
    [
        {"timestamp": "2024-05-01T00:00:00", "pm25_density": 22.5},
        ...
    ]
    """
    history_df = preprocess_history(history)
    forecast = forecast_48h(history_df)
    return {"predictions": forecast}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
