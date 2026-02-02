import json
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

# Suppress warnings
warnings.filterwarnings("ignore")

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
        "pipeline_file": "pm25_pipeline_best_model.pkl",
        "density_col": "pm25_density",
        "x_points": np.array([0.0, 15.5, 55.4, 150.4, 250.4, 500.0]),
    },
    "pm10": {
        "pipeline_file": "pm10_pipeline_best_model.pkl",
        "density_col": "pm10_density",
        "x_points": np.array([0.0, 50, 150, 350, 420, 10000]),
    }
}
Y_POINTS = np.array([0, 50, 100, 200, 300, 500])

# ========================================
# ISPU CALCULATOR FOR IMPUTATION
# ========================================
BREAKPOINTS = {
    'PM25': [
        [0.0, 15.5, 0, 50],         # Baik
        [15.6, 55.4, 51, 100],      # Sedang
        [55.5, 150.4, 101, 200],    # Tidak Sehat
        [150.5, 250.4, 201, 300],   # Sangat Tidak Sehat
        [250.5, 500.0, 301, 500]    # Berbahaya
    ],
    'PM10': [
        [0, 50, 0, 50],             # Baik
        [51, 150, 51, 100],         # Sedang
        [151, 350, 101, 200],       # Tidak Sehat
        [351, 420, 201, 300],       # Sangat Tidak Sehat
        [421, 10000, 301, 500]      # Berbahaya
    ]
}

def hitung_ispu(konsentrasi, polutan='PM25'):
    """Menghitung ISPU menggunakan interpolasi linear."""
    if konsentrasi is None or pd.isna(konsentrasi): return None
    if konsentrasi < 0: return 0.0
    breakpoints = BREAKPOINTS[polutan]
    for bp in breakpoints:
        Xl, Xu, Il, Iu = bp
        if Xl <= konsentrasi <= Xu:
            ispu = ((Iu - Il) / (Xu - Xl)) * (konsentrasi - Xl) + Il
            return round(ispu, 2)
    return 500.0

def detect_anomaly(value, mean, std, iqr_low, iqr_high, method='combined'):
    """Deteksi apakah nilai adalah anomali/tidak normal"""
    if pd.isna(value) or value < 0: return True
    z_score = abs((value - mean) / std) if std > 0 else 0
    is_zscore_anomaly = z_score > 3
    is_iqr_anomaly = (value < iqr_low) or (value > iqr_high)
    if method == 'zscore': return is_zscore_anomaly
    elif method == 'iqr': return is_iqr_anomaly
    else: return is_zscore_anomaly or is_iqr_anomaly

# Global storage for models
model_params = {}
pipelines = {}
imputer = None

class RidgeLite:
    """Implementasi Ridge Regression tanpa scikit-learn"""
    def __init__(self, coef, intercept):
        self.coef = np.array(coef)
        self.intercept = intercept
    
    def predict(self, X):
        # X can be DataFrame or numpy array
        if isinstance(X, pd.DataFrame):
            X = X.values
        return np.dot(X, self.coef) + self.intercept

class ScalerLite:
    """Implementasi StandardScaler tanpa scikit-learn"""
    def __init__(self, mean, scale):
        self.mean = np.array(mean)
        self.scale = np.array(scale)
    
    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X = X.values
        return (X - self.mean) / self.scale

class AirQualityImputer:
    """Complete system untuk imputation data kualitas udara (Tanpa sklearn)"""
    def __init__(self, params, stats):
        self.pm25_model = RidgeLite(params['pm25_model']['coef'], params['pm25_model']['intercept'])
        self.pm25_scaler = ScalerLite(params['pm25_scaler']['mean'], params['pm25_scaler']['scale'])
        self.pm10_model = RidgeLite(params['pm10_model']['coef'], params['pm10_model']['intercept'])
        self.pm10_scaler = ScalerLite(params['pm10_scaler']['mean'], params['pm10_scaler']['scale'])
        self.pm25_stats = stats['pm25_stats']
        self.pm10_stats = stats['pm10_stats']
    
    def is_anomaly(self, value, pollutant='pm25'):
        stats = self.pm25_stats if pollutant == 'pm25' else self.pm10_stats
        return detect_anomaly(value, stats['mean'], stats['std'],
                            stats['iqr_low'], stats['iqr_high'])
    
    def impute_pm25(self, pm10, temperature, humidity, pressure):
        input_data = np.array([[pm10, temperature, humidity, pressure]])
        input_scaled = self.pm25_scaler.transform(input_data)
        predicted = self.pm25_model.predict(input_scaled)[0]
        return max(0.0, predicted)
    
    def impute_pm10(self, pm25, temperature, humidity, pressure):
        input_data = np.array([[pm25, temperature, humidity, pressure]])
        input_scaled = self.pm10_scaler.transform(input_data)
        predicted = self.pm10_model.predict(input_scaled)[0]
        return max(0.0, predicted)
    
    def process_reading(self, pm25_raw, pm10_raw, temperature, humidity, pressure):
        result = {
            'pm25_raw': pm25_raw, 'pm10_raw': pm10_raw,
            'pm25_final': pm25_raw, 'pm10_final': pm10_raw,
            'pm25_imputed': False, 'pm10_imputed': False,
            'pm25_status': 'normal', 'pm10_status': 'normal'
        }
        pm25_is_anomaly = self.is_anomaly(pm25_raw, 'pm25')
        pm10_is_anomaly = self.is_anomaly(pm10_raw, 'pm10')
        
        if pm25_is_anomaly and pm10_is_anomaly:
            result.update({'pm25_final': self.pm25_stats['mean'], 'pm10_final': self.pm10_stats['mean'],
                          'pm25_imputed': True, 'pm10_imputed': True,
                          'pm25_status': 'anomaly_both_bad', 'pm10_status': 'anomaly_both_bad'})
        elif pm25_is_anomaly:
            result.update({'pm25_final': self.impute_pm25(pm10_raw, temperature, humidity, pressure),
                          'pm25_imputed': True, 'pm25_status': 'anomaly_imputed'})
        elif pm10_is_anomaly:
            result.update({'pm10_final': self.impute_pm10(pm25_raw, temperature, humidity, pressure),
                          'pm10_imputed': True, 'pm10_status': 'anomaly_imputed'})
        return result

def load_models():
    """Load model parameters from JSON"""
    global model_params, pipelines, imputer
    
    json_path = Path(__file__).resolve().parent / "model_params.json"
    if not json_path.exists():
        print("Error: model_params.json not found!")
        return

    with open(json_path, 'r') as f:
        model_params = json.load(f)
    
    # Setup Prediction Pipelines
    for p_type in ["pm25", "pm10"]:
        key = f"{p_type}_pred"
        if key in model_params:
            data = model_params[key]
            pipelines[p_type] = {
                "model": RidgeLite(data["coef"], data["intercept"]),
                "features": data["features"],
                "lags": [1, 2, 3, 6, 12, 24, 48],
                "rolls": [3, 6, 12, 24, 48],
                "max_lookback": 49
            }
            print(f"Loaded {p_type} prediction model")
    
    # Setup Imputer
    if "imputer" in model_params and "anomaly_stats" in model_params:
        imputer = AirQualityImputer(model_params["imputer"], model_params["anomaly_stats"])
        print("Loaded imputer model")

# Load models on startup
load_models()


class HistoryItem(BaseModel):
    timestamp: datetime
    pm25_density: Optional[float] = None
    pm10_density: Optional[float] = None

class PredictRequest(BaseModel):
    pollutant: str = Field(..., description="Tipe polutan: 'pm25' atau 'pm10'")
    history: List[HistoryItem]

class IoTReading(BaseModel):
    pm25: Optional[float] = Field(None, description="PM2.5 density (µg/m³)")
    pm10: Optional[float] = Field(None, description="PM10 density (µg/m³)")
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Humidity (%)")
    pressure: float = Field(..., description="Pressure (hPa)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of reading")

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
    
    try:
        history_df = preprocess_history(request.history, p_type)
        feature_df = add_features(history_df, p_type).dropna()
        if feature_df.empty:
            raise HTTPException(status_code=400, detail="Data historis tidak cukup setelah feature engineering.")
        
        p_info = pipelines[p_type]
        latest_features = feature_df.iloc[[-1]][p_info["features"]]
        latest_aqi = float(p_info["model"].predict(latest_features)[0])
        forecast = forecast_48h(history_df, p_type)
        
        return {
            "success": True,
            "pollutant": p_type,
            "latest_timestamp": feature_df.index[-1].isoformat(),
            "predicted_aqi": round(max(0, latest_aqi), 2),
            "forecast_48h": forecast
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error melakukan prediksi: {str(e)}")

@app.post("/impute")
def impute_reading(reading: IoTReading):
    """
    Endpoint untuk data imputation dari IoT sensor
    
    Fungsi:
    - Deteksi anomali pada PM2.5 dan PM10
    - Impute nilai yang error atau tidak normal
    - Return data yang sudah diproses dengan ISPU
    """
    if imputer is None:
        raise HTTPException(
            status_code=503, 
            detail="Imputer model tidak tersedia. Model belum dimuat atau gagal dimuat saat startup."
        )
    
    try:
        # Process reading dengan imputer
        result = imputer.process_reading(
            pm25_raw=reading.pm25,
            pm10_raw=reading.pm10,
            temperature=reading.temperature,
            humidity=reading.humidity,
            pressure=reading.pressure
        )
        
        # Hitung ISPU
        ispu_pm25 = hitung_ispu(result['pm25_final'], 'PM25')
        ispu_pm10 = hitung_ispu(result['pm10_final'], 'PM10')
        ispu = max(ispu_pm25, ispu_pm10) if ispu_pm25 and ispu_pm10 else (ispu_pm25 or ispu_pm10 or 0)
        
        # Determine air quality level
        air_quality_level = "Baik"
        if ispu > 300:
            air_quality_level = "Berbahaya"
        elif ispu > 200:
            air_quality_level = "Sangat Tidak Sehat"
        elif ispu > 100:
            air_quality_level = "Tidak Sehat"
        elif ispu > 50:
            air_quality_level = "Sedang"
        
        return {
            "success": True,
            "timestamp": reading.timestamp.isoformat(),
            "raw_data": {
                "pm25": result['pm25_raw'],
                "pm10": result['pm10_raw']
            },
            "processed_data": {
                "pm25": round(result['pm25_final'], 2),
                "pm10": round(result['pm10_final'], 2),
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "pressure": reading.pressure
            },
            "ispu": {
                "pm25": round(ispu_pm25, 2) if ispu_pm25 else None,
                "pm10": round(ispu_pm10, 2) if ispu_pm10 else None,
                "overall": round(ispu, 2)
            },
            "air_quality_level": air_quality_level,
            "imputation_status": {
                "pm25_imputed": result['pm25_imputed'],
                "pm10_imputed": result['pm10_imputed'],
                "pm25_status": result['pm25_status'],
                "pm10_status": result['pm10_status']
            },
            "warnings": [
                f"⚠️ PM2.5 was imputed ({result['pm25_status']})" if result['pm25_imputed'] else None,
                f"⚠️ PM10 was imputed ({result['pm10_status']})" if result['pm10_imputed'] else None
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing reading: {str(e)}")

@app.get("/status")
def get_status():
    """Mengecek status model yang aktif"""
    return {
        "active_models": list(pipelines.keys()),
        "imputer_loaded": imputer is not None,
        "configurations": {k: {"features": len(v["features"])} for k, v in pipelines.items()},
        "endpoints": {
            "prediction": "/predict - Prediksi AQI 48 jam ke depan",
            "imputation": "/impute - Data imputation untuk IoT sensor",
            "status": "/status - Cek status model"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_simple:app", host="0.0.0.0", port=8001, reload=True)
