
import json
import numpy as np
import pandas as pd
import warnings
import os
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Suppress warnings
warnings.filterwarnings("ignore")

app = FastAPI(
    title="Hawa ISPU Prediction API (Tuned)",
    description="API untuk prediksi ISPU menggunakan model ElasticNet yang sudah di-tune",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RidgeLite:
    """Implementasi Linear Model (Ridge/ElasticNet) tanpa scikit-learn"""
    def __init__(self, coef, intercept):
        self.coef = np.array(coef)
        self.intercept = intercept
    
    def predict(self, X):
        return np.dot(X, self.coef) + self.intercept

class ScalerLite:
    """Implementasi StandardScaler tanpa scikit-learn"""
    def __init__(self, mean, scale):
        self.mean = np.array(mean)
        self.scale = np.array(scale)
    
    def transform(self, X):
        return (X - self.mean) / self.scale

# Global model storage
model_config = None
model = None
scaler = None

def pm10_to_ispu(pm10):
    """
    Konversi konsentrasi PM10 ke nilai ISPU (Permen LHK No. 14 Tahun 2020)
    """
    if pm10 <= 50:
        return (50/50) * (pm10 - 0) + 0
    elif pm10 <= 150:
        return (50/100) * (pm10 - 50) + 50
    elif pm10 <= 350:
        return (100/200) * (pm10 - 150) + 100
    elif pm10 <= 420:
        return (100/70) * (pm10 - 350) + 200
    elif pm10 <= 500:
        return (100/80) * (pm10 - 420) + 300
    else:
        # Untuk nilai > 500, menggunakan ekstrapolasi linear sederhana
        return (100/80) * (pm10 - 500) + 400

def pm25_to_ispu(pm25):
    """
    Konversi konsentrasi PM2.5 ke nilai ISPU (Permen LHK No. 14 Tahun 2020)
    """
    if pm25 <= 15.5:
        return (50/15.5) * (pm25 - 0) + 0
    elif pm25 <= 55.4:
        return (50/(55.4-15.5)) * (pm25 - 15.5) + 50
    elif pm25 <= 150.4:
        return (100/(150.4-55.4)) * (pm25 - 55.4) + 100
    elif pm25 <= 250.4:
        return (100/(250.4-150.4)) * (pm25 - 150.4) + 200
    elif pm25 <= 500:
        return (200/(500-250.4)) * (pm25 - 250.4) + 300
    else:
        # Untuk nilai > 500
        return (100/100) * (pm25 - 500) + 500

def calculate_aqi_ispu(pm10, pm25):
    """
    Menghitung nilai ISPU akhir berdasarkan nilai tertinggi antara PM10 dan PM2.5
    """
    ispu_pm10 = pm10_to_ispu(pm10)
    ispu_pm25 = pm25_to_ispu(pm25)
    return max(ispu_pm10, ispu_pm25)

def load_model():
    global model_config, model, scaler
    json_path = Path(__file__).resolve().parent / "model_config.json"
    if not json_path.exists():
        print(f"Error: {json_path} not found!")
        return False

    with open(json_path, 'r') as f:
        model_config = json.load(f)
    
    params = model_config['model_params']
    scaler_params = model_config['scaler']
    
    model = RidgeLite(params['coefficients'], params['intercept'])
    scaler = ScalerLite(scaler_params['mean'], scaler_params['scale'])
    print(f"SUCCESS: Model {model_config['model_type']} loaded with {len(model_config['feature_cols'])} features")
    return True

# Load model on startup
load_model()

def create_features_lite(df_input, target_col='aqi_ispu', pm_cols=['PM10_ug_m3', 'PM2.5_ug_m3']):
    """
    Re-implementasi create_features dari notebook untuk kebutuhan inference.
    df_input harus memiliki index datetime dan kolom yang diperlukan.
    """
    df = df_input.copy()
    
    # 1. LAG FEATURES
    lag_periods = [1, 2, 3, 4, 6, 8, 12, 18, 24]
    for lag in lag_periods:
        df[f'ispu_lag_{lag}h'] = df[target_col].shift(lag)
        for pm_col in pm_cols:
            df[f'{pm_col}_lag_{lag}h'] = df[pm_col].shift(lag)
    
    # 2. ROLLING STATISTICS
    windows = [3, 6, 8, 12, 18, 24]
    for window in windows:
        df[f'ispu_rolling_mean_{window}h'] = df[target_col].rolling(window).mean()
        df[f'ispu_rolling_std_{window}h'] = df[target_col].rolling(window).std()
        df[f'ispu_rolling_min_{window}h'] = df[target_col].rolling(window).min()
        df[f'ispu_rolling_max_{window}h'] = df[target_col].rolling(window).max()
        df[f'ispu_rolling_median_{window}h'] = df[target_col].rolling(window).median()
        df[f'ispu_rolling_range_{window}h'] = df[target_col].rolling(window).max() - df[target_col].rolling(window).min()
        
        for pm_col in pm_cols:
            df[f'{pm_col}_rolling_mean_{window}h'] = df[pm_col].rolling(window).mean()
            df[f'{pm_col}_rolling_std_{window}h'] = df[pm_col].rolling(window).std()
            df[f'{pm_col}_rolling_median_{window}h'] = df[pm_col].rolling(window).median()
    
    # 3. EWMA
    ewm_spans = [6, 12, 24]
    for span in ewm_spans:
        df[f'ispu_ewm_{span}h'] = df[target_col].ewm(span=span).mean()
        df[f'ispu_ewm_std_{span}h'] = df[target_col].ewm(span=span).std()
        for pm_col in pm_cols:
            df[f'{pm_col}_ewm_{span}h'] = df[pm_col].ewm(span=span).mean()
    
    # 4. TIME-BASED FEATURES
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['month'] = df.index.month
    df['dayofyear'] = df.index.dayofyear
    df['weekofyear'] = df.index.isocalendar().week.astype(int)
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
    df['is_rush_hour'] = ((df['hour'] >= 7) & (df['hour'] <= 9) | (df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
    
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    
    # 5. TREND FEATURES
    df['ispu_diff_1h'] = df[target_col].diff(1)
    df['ispu_diff_3h'] = df[target_col].diff(3)
    df['ispu_diff_6h'] = df[target_col].diff(6)
    df['ispu_diff_12h'] = df[target_col].diff(12)
    df['ispu_diff_24h'] = df[target_col].diff(24)
    
    df['ispu_pct_change_1h'] = df[target_col].pct_change(1)
    df['ispu_pct_change_3h'] = df[target_col].pct_change(3)
    df['ispu_pct_change_6h'] = df[target_col].pct_change(6)
    
    # 6. INTERACTION FEATURES
    df['pm_ratio'] = df['PM2.5_ug_m3'] / (df['PM10_ug_m3'] + 1)
    df['pm_sum'] = df['PM2.5_ug_m3'] + df['PM10_ug_m3']
    df['pm_diff'] = df['PM10_ug_m3'] - df['PM2.5_ug_m3']
    df['pm_product'] = df['PM2.5_ug_m3'] * df['PM10_ug_m3']
    
    # 7. VOLATILITY FEATURES
    for window in [6, 12, 24]:
        df[f'ispu_volatility_{window}h'] = df[target_col].rolling(window).std() / (df[target_col].rolling(window).mean() + 1)
    
    # 8. MOMENTUM FEATURES
    for window in [6, 12, 24]:
        df[f'ispu_momentum_{window}h'] = df[target_col] - df[target_col].shift(window)
    
    # 9. ZSCORE FEATURES
    for window in [12, 24]:
        rolling_mean = df[target_col].rolling(window).mean()
        rolling_std = df[target_col].rolling(window).std()
        df[f'ispu_zscore_{window}h'] = (df[target_col] - rolling_mean) / (rolling_std + 1e-8)
    
    return df

class HistoryItem(BaseModel):
    timestamp: str
    pm25: float = Field(..., alias="PM2.5_ug_m3")
    pm10: float = Field(..., alias="PM10_ug_m3")

class PredictRequest(BaseModel):
    history: List[HistoryItem]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "model_type": model_config['model_type'] if model_config else "Not Loaded",
        "version": "2.0.0 (Lightweight JSON)"
    }

@app.post("/predict")
def predict(request: PredictRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # 1. Convert history to DataFrame
        data = []
        for item in request.history:
            data.append({
                "timestamp": item.timestamp,
                "PM2.5_ug_m3": item.pm25,
                "PM10_ug_m3": item.pm10
            })
        
        df = pd.DataFrame(data)
        
        # Tambahkan kolom aqi_ispu kosong jika belum ada agar tidak error saat resampling
        if 'aqi_ispu' not in df.columns:
            df['aqi_ispu'] = np.nan
        
        # Konversi timestamp dengan penanganan format yang fleksibel
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Hapus data dengan timestamp tidak valid
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Tidak ada data valid yang bisa diproses.")

        df = df.sort_values('timestamp').set_index('timestamp')
        
        # Cek rentang waktu data (minimal 24 jam)
        duration = df.index.max() - df.index.min()
        if duration < timedelta(hours=23, minutes=50): # Toleransi sedikit
            raise HTTPException(
                status_code=400, 
                detail=f"Rentang waktu data hanya {duration}. Dibutuhkan minimal 24 jam data historis."
            )

        # 2. Resample high-frequency data (30s, 1m, dll) ke rata-rata per jam
        # '1h' resample akan mengelompokkan data berdasarkan jam (00:00, 01:00, dst)
        df_hourly = df.resample('1h').mean()
        
        # Isi gap jika ada jam yang kosong menggunakan interpolasi linear
        # Limit 3 jam untuk menghindari interpolasi pada gap yang terlalu besar
        df_hourly = df_hourly.interpolate(method='linear', limit=3)
        
        # Tambahkan kolom aqi_ispu yang akan diisi
        df_hourly['aqi_ispu'] = np.nan

        # Hitung ulang ISPU pada data rata-rata per jam
        # Ini penting karena ISPU(rata-rata PM) != rata-rata(ISPU)
        for idx, row in df_hourly.iterrows():
            # Selalu hitung ulang ISPU berdasarkan PM rata-rata per jam untuk akurasi model
            if not pd.isna(row['PM10_ug_m3']) and not pd.isna(row['PM2.5_ug_m3']):
                df_hourly.at[idx, 'aqi_ispu'] = calculate_aqi_ispu(row['PM10_ug_m3'], row['PM2.5_ug_m3'])
        
        # Drop rows yang masih memiliki NaN (gap > 3 jam atau di ujung data)
        df_hourly = df_hourly.dropna()
        
        # Cek kembali kecukupan data setelah resampling & dropna
        if len(df_hourly) < 24:
            raise HTTPException(
                status_code=400, 
                detail=f"Data hasil agregasi per jam hanya tersedia {len(df_hourly)} jam (setelah menangani gap). Minimal dibutuhkan 24 jam data tanpa gap besar."
            )
            
        # Gunakan hanya 24 jam terakhir untuk fitur rolling agar konsisten
        df_hourly = df_hourly.tail(24)
            
        # 3. Create features menggunakan data per jam
        df_features = create_features_lite(df_hourly)
        
        # Tangani nilai NaN/Inf yang muncul dari perhitungan fitur (lag, diff, dll)
        df_features = df_features.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Ambil baris terakhir untuk prediksi
        latest_features_row = df_features.iloc[-1:]
        
        # 3. Select only required features in correct order
        X_input = latest_features_row[model_config['feature_cols']]
        
        # 4. Scaling
        X_scaled = scaler.transform(X_input)
        
        # 5. Predict
        prediction = model.predict(X_scaled)[0]
        
        # Pastikan prediction bukan NaN
        if np.isnan(prediction) or np.isinf(prediction):
            prediction = df['aqi_ispu'].iloc[-1] # Fallback ke nilai terakhir jika model gagal
        
        # 6. Generate 48h forecast (Simple autoregressive simulation for demo)
        # In real case, we might need a multi-step model, but here we simulate based on trend
        last_aqi = df_hourly['aqi_ispu'].iloc[-1]
        trend = (prediction - last_aqi) / 1.0 # simple 1h trend
        
        forecast = []
        current_time = df.index[-1]
        current_val = prediction
        
        for i in range(1, 49):
            # Add some slight decay to trend over time
            current_val += trend * (0.95 ** i) 
            # Keep within reasonable ISPU bounds
            current_val = max(0, min(500, current_val))
            
            forecast.append({
                "hour": i,
                "timestamp": (current_time + timedelta(hours=i)).isoformat(),
                "predicted_aqi": round(float(current_val), 2)
            })
            
        return {
            "success": True,
            "prediction": round(float(prediction), 2),
            "forecast_48h": forecast,
            "model_info": {
                "type": model_config['model_type'],
                "features_used": len(model_config['feature_cols'])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
