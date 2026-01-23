import joblib
import numpy as np
import pandas as pd
import warnings
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Suppress XGBoost version warnings
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")

# Model URLs - GANTI DENGAN URL MODEL ANDA
MODEL_URLS = {
    "pm25": os.getenv("PM25_MODEL_URL", "https://github.com/AriAnanta/Hawa-ML/releases/download/v1.0.0/pm25_pipeline_enhanced.pkl"),
    "pm10": os.getenv("PM10_MODEL_URL", "https://github.com/AriAnanta/Hawa-ML/releases/download/v1.0.0/pm10_pipeline_enhanced.pkl")
}

app = FastAPI(
    title="AQI Prediction API (PM2.5 & PM10)",
    description="API untuk prediksi AQI (ISPU) 48 jam ke depan untuk polutan PM2.5 dan PM10",
    version="1.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for Pollutants
POLLUTANT_CONFIG = {
    "pm25": {
        "pipeline_file": "pm25_pipeline_enhanced.pkl",
        "density_col": "pm25_density",
        "x_points": np.array([0.0, 15.5, 55.4, 150.4, 250.4, 500.0]),
    },
    "pm10": {
        "pipeline_file": "pm10_pipeline_enhanced.pkl",
        "density_col": "pm10_density",
        "x_points": np.array([0.0, 50, 150, 350, 420, 10000]),
    }
}
Y_POINTS = np.array([0, 50, 100, 200, 300, 500])

# Global storage for models and features
pipelines = {}

def download_model(url: str, local_path: Path) -> bool:
    """Download model dari URL eksternal"""
    try:
        if local_path.exists():
            print(f"Model sudah ada di {local_path}")
            return True
        
        print(f"Downloading model dari {url}...")
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Model berhasil didownload ke {local_path}")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

def load_pipelines():
    """Memuat semua pipeline model yang tersedia (PM2.5 dan PM10)"""
    # Gunakan /tmp untuk serverless environment
    base_path = Path("/tmp") if os.getenv("VERCEL") else Path(__file__).resolve().parent
    
    for p_type, config in POLLUTANT_CONFIG.items():
        local_path = base_path / config["pipeline_file"]
        
        # Cek apakah file lokal ada, jika tidak download dari URL
        if not local_path.exists():
            model_url = MODEL_URLS.get(p_type)
            if model_url and model_url != f"YOUR_{p_type.upper()}_MODEL_URL_HERE":
                if not download_model(model_url, local_path):
                    print(f"Gagal download model {p_type}, mencoba load dari local...")
                    # Fallback ke folder lokal jika download gagal
                    local_path = Path(__file__).resolve().parent / config["pipeline_file"]
        
        if local_path.exists():
            try:
                data = joblib.load(local_path)
                pipelines[p_type] = {
                    "model": data["model"],
                    "features": data["features"],
                    "lags": data.get("lags", [1, 2, 3, 6, 12, 24, 48]),
                    "rolls": data.get("rolls", [3, 6, 12, 24, 48]),
                    "max_lookback": max(max(data.get("lags", [48])), max(data.get("rolls", [48]))) + 1
                }
                print(f"Berhasil memuat model {p_type} dari {config['pipeline_file']}")
            except Exception as e:
                print(f"Gagal memuat model {p_type}: {e}")
        else:
            print(f"Peringatan: File pipeline {local_path} tidak ditemukan dan tidak bisa didownload.")


# Load models on startup
load_pipelines()

class HistoryItem(BaseModel):
    timestamp: datetime
    pm25_density: Optional[float] = None
    pm10_density: Optional[float] = None

class PredictRequest(BaseModel):
    pollutant: str = Field(..., description="Tipe polutan: 'pm25' atau 'pm10'")
    history: List[HistoryItem]

def preprocess_history(items: List[HistoryItem], p_type: str) -> pd.DataFrame:
    """Preprosessing data historis sesuai dengan tipe polutan"""
    if not items:
        raise HTTPException(status_code=400, detail="Data historis kosong")
    
    config = POLLUTANT_CONFIG[p_type]
    density_col = config["density_col"]
    
    df = pd.DataFrame([i.model_dump() for i in items])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").set_index("timestamp")
    
    # Pastikan kolom densitas yang sesuai ada
    if density_col not in df.columns or df[density_col].isnull().all():
        # Fallback: jika user mengirim pm25_density tapi minta pm10, atau sebaliknya
        other_col = "pm10_density" if density_col == "pm25_density" else "pm25_density"
        if other_col in df.columns and not df[other_col].isnull().all():
            df[density_col] = df[other_col]
        else:
            raise HTTPException(status_code=400, detail=f"Kolom {density_col} tidak ditemukan dalam data")

    df = df[[density_col]].copy()
    
    # Hitung AQI/ISPU
    df["aqi_ispu"] = np.interp(df[density_col], config["x_points"], Y_POINTS)
    
    # Resample ke per jam
    df_resampled = df.resample("1h").mean().ffill()
    
    max_lookback = pipelines[p_type]["max_lookback"]
    if len(df_resampled) < max_lookback:
        raise HTTPException(
            status_code=400, 
            detail=f"Data tidak mencukupi untuk {p_type}. Tersedia {len(df_resampled)} jam, butuh minimal {max_lookback} jam."
        )
    
    return df_resampled.tail(max_lookback)

def add_features(df: pd.DataFrame, p_type: str) -> pd.DataFrame:
    """Feature engineering dinamis berdasarkan tipe polutan"""
    df = df.copy()
    p_info = pipelines[p_type]
    density_col = POLLUTANT_CONFIG[p_type]["density_col"]
    
    # Time features
    df["hour"] = df.index.hour
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month
    df["weekofyear"] = df.index.isocalendar().week.astype(int)
    df["dayofyear"] = df.index.dayofyear
    
    # Lags
    for l in p_info["lags"]:
        df[f"aqi_lag_{l}"] = df["aqi_ispu"].shift(l)
        # Menyesuaikan nama kolom lag densitas (pm25_lag_x atau pm10_lag_x)
        # Sesuai dengan apa yang diharapkan model di notebook
        prefix = "pm25" if p_type == "pm25" else "pm10"
        df[f"{prefix}_lag_{l}"] = df[density_col].shift(l)
    
    # Rolling windows
    for r in p_info["rolls"]:
        df[f"aqi_roll_mean_{r}"] = df["aqi_ispu"].rolling(r).mean()
        df[f"aqi_roll_std_{r}"] = df["aqi_ispu"].rolling(r).std()
    
    return df

def forecast_48h(history: pd.DataFrame, p_type: str) -> list:
    """Melakukan peramalan 48 jam secara rekursif"""
    current = history.copy()
    p_info = pipelines[p_type]
    density_col = POLLUTANT_CONFIG[p_type]["density_col"]
    results = []
    last_timestamp = current.index[-1]
    
    for i in range(1, 49):
        next_time = last_timestamp + timedelta(hours=i)
        next_row = pd.DataFrame(index=[next_time], columns=current.columns, dtype=float)
        
        # Skenario simpel: densitas dianggap konstan untuk prediksi AQI
        next_row[density_col] = current[density_col].iloc[-1]
        next_row["aqi_ispu"] = np.nan
        
        temp = pd.concat([current, next_row])
        df_feat = add_features(temp, p_type).dropna()
        
        X_next = df_feat.iloc[[-1]][p_info["features"]]
        pred_aqi = float(p_info["model"].predict(X_next)[0])
        
        results.append({
            "timestamp": next_time.isoformat(),
            "predicted_aqi": round(max(0, pred_aqi), 2) # AQI tidak boleh negatif
        })
        
        temp.loc[next_time, "aqi_ispu"] = pred_aqi
        current = temp
    
    return results

@app.post("/predict")
def predict(request: PredictRequest):
    """
    Endpoint utama untuk prediksi AQI (PM2.5 atau PM10)
    """
    p_type = request.pollutant.lower()
    if p_type not in pipelines:
        raise HTTPException(status_code=400, detail=f"Model untuk polutan '{p_type}' belum dimuat atau tidak didukung.")
    
    history_df = preprocess_history(request.history, p_type)
    forecast = forecast_48h(history_df, p_type)
    
    return {
        "pollutant": p_type,
        "predictions": forecast
    }

@app.get("/status")
def get_status():
    """Mengecek status model yang aktif"""
    return {
        "active_models": list(pipelines.keys()),
        "configurations": {k: {"features": len(v["features"])} for k, v in pipelines.items()}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_simple:app", host="0.0.0.0", port=8001, reload=True)
