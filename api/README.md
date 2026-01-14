# 🌤️ AQI Prediction API - Enhanced

API REST untuk prediksi Air Quality Index (AQI/ISPU) selama 48 jam ke depan menggunakan XGBoost dan Recursive Forecasting.

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Teknologi](#-teknologi)
- [Instalasi](#-instalasi)
- [Menjalankan API](#-menjalankan-api)
- [Endpoints](#-endpoints)
- [Contoh Penggunaan](#-contoh-penggunaan)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

## ✨ Fitur

- **Prediksi 48 Jam**: Prediksi AQI untuk 48 jam mendatang dengan interval per jam
- **Recursive Forecasting**: Menggunakan prediksi sebelumnya untuk prediksi berikutnya
- **Feature Engineering**: 
  - Lag features (1, 2, 3, 6, 12, 24, 48 jam)
  - Rolling statistics (mean & std untuk window 3, 6, 12, 24, 48)
  - Time-based features (hour, day of week, month, dll)
- **ISPU Standard**: Menggunakan standar Indeks Standar Pencemar Udara Indonesia
- **Kategori AQI**: Klasifikasi otomatis (Good, Moderate, Unhealthy, dll)
- **Health Advice**: Rekomendasi kesehatan berdasarkan level AQI
- **Interactive Docs**: Swagger UI dan ReDoc terintegrasi
- **CORS Enabled**: Siap diakses dari frontend aplikasi

## 🔧 Teknologi

- **FastAPI**: Framework web modern dan cepat
- **XGBoost**: Model machine learning dengan regularisasi
- **Pandas & NumPy**: Data processing
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## 📦 Instalasi

### Prerequisites

- Python 3.8 atau lebih baru
- pip (Python package manager)
- Model terlatih: `aqi_pipeline_enhanced.pkl`

### Langkah Instalasi

1. **Clone repository** (jika belum):
```bash
git clone <your-repo-url>
cd ai-sl2
```

2. **Install dependencies**:
```bash
pip install -r api/requirements.txt
```

Atau install manual:
```bash
pip install fastapi uvicorn pandas numpy scikit-learn xgboost joblib pydantic
```

3. **Pastikan model tersedia**:
   - File `aqi_pipeline_enhanced.pkl` harus ada di direktori root project
   - Jalankan notebook `prediction_AQI_Untuk_API_Enhanced.ipynb` untuk melatih model jika belum ada

## 🚀 Menjalankan API

### Development Mode (dengan auto-reload):

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Dengan Custom Port:

```bash
uvicorn api.app:app --reload --port 5000
```

API akan berjalan di: **http://localhost:8000**

## 📚 Endpoints

### 1. Root Endpoint
**GET** `/`

Informasi dasar tentang API.

**Response:**
```json
{
  "message": "AQI Prediction API - Enhanced",
  "version": "2.0.0",
  "endpoints": {
    "health": "/health",
    "docs": "/docs",
    "predict": "/predict"
  }
}
```

---

### 2. Health Check
**GET** `/health`

Memeriksa status API dan informasi model.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "max_lookback_hours": 49,
  "model_info": {
    "lags": [1, 2, 3, 6, 12, 24, 48],
    "rolls": [3, 6, 12, 24, 48],
    "features_count": 39,
    "model_type": "XGBoost Regressor"
  }
}
```

---

### 3. Predict AQI (Full)
**POST** `/predict`

Prediksi AQI untuk 48 jam ke depan dengan informasi lengkap.

**Request Body:**
```json
[
  {
    "timestamp": "2024-05-01T00:00:00",
    "pm25_density": 22.5,
    "aqi_ispu": 73.2
  },
  {
    "timestamp": "2024-05-01T01:00:00",
    "pm25_density": 24.1
  }
  // ... minimal 49 data points
]
```

**Parameters:**
- `timestamp` (string, required): Timestamp dalam format ISO 8601
- `pm25_density` (float, required): Konsentrasi PM2.5 dalam µg/m³ (0-1000)
- `aqi_ispu` (float, optional): AQI/ISPU yang sudah dihitung (0-500)

**Response:**
```json
{
  "forecast": [
    {
      "timestamp": "2024-05-02T01:00:00",
      "pred_aqi": 87.4,
      "category": "Moderate",
      "health_advice": "Air quality is acceptable..."
    }
  ],
  "metadata": {
    "horizon_hours": 48,
    "required_history_hours": 49,
    "features_used": 39,
    "model_type": "XGBoost Regressor",
    "prediction_time": "2024-05-01T15:30:00"
  },
  "statistics": {
    "mean_aqi": 88.5,
    "min_aqi": 75.2,
    "max_aqi": 102.3,
    "std_aqi": 8.4,
    "median_aqi": 87.0
  }
}
```

---

### 4. Predict AQI (Simplified)
**POST** `/predict/simple`

Prediksi AQI sederhana tanpa kategori dan health advice.

**Request Body:** (sama dengan `/predict`)

**Response:**
```json
{
  "forecast": [
    {
      "timestamp": "2024-05-02T01:00:00",
      "pred_aqi": 87.4
    }
  ],
  "metadata": {
    "horizon_hours": 48,
    "required_history_hours": 49
  }
}
```

---

### 📊 AQI Categories (ISPU Standard)

| AQI Range | Category | Description |
|-----------|----------|-------------|
| 0-50 | Good | Kualitas udara baik |
| 51-100 | Moderate | Kualitas udara sedang |
| 101-200 | Unhealthy | Tidak sehat |
| 201-300 | Very Unhealthy | Sangat tidak sehat |
| 300+ | Hazardous | Berbahaya |

## 🔍 Contoh Penggunaan

### Menggunakan cURL

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d @api/sample_payload.json
```

### Menggunakan Python (requests)

```python
import requests
import json
from datetime import datetime, timedelta

# Prepare historical data
base_time = datetime(2024, 5, 1, 0, 0, 0)
history = []

for i in range(50):  # 50 hours of data
    history.append({
        "timestamp": (base_time + timedelta(hours=i)).isoformat(),
        "pm25_density": 20 + (i % 10) * 2  # Simulated data
    })

# Make prediction request
response = requests.post(
    "http://localhost:8000/predict",
    json=history
)

if response.status_code == 200:
    result = response.json()
    print(f"Mean AQI: {result['statistics']['mean_aqi']:.2f}")
    
    # Print first 5 predictions
    for pred in result['forecast'][:5]:
        print(f"{pred['timestamp']}: {pred['pred_aqi']:.2f} ({pred['category']})")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Menggunakan JavaScript (fetch)

```javascript
const history = [
  // Your historical data (min 49 points)
  { timestamp: "2024-05-01T00:00:00", pm25_density: 22.5 },
  { timestamp: "2024-05-01T01:00:00", pm25_density: 24.1 },
  // ... more data
];

fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(history)
})
.then(response => response.json())
.then(data => {
  console.log('Mean AQI:', data.statistics.mean_aqi);
  console.log('Forecast:', data.forecast);
})
.catch(error => console.error('Error:', error));
```

## 🧪 Testing

Jalankan test script:

```bash
python api/test_api.py
```

Atau gunakan Swagger UI:
1. Buka browser: http://localhost:8000/docs
2. Pilih endpoint `/predict`
3. Klik "Try it out"
4. Gunakan sample data atau upload `sample_payload.json`
5. Klik "Execute"

## ❗ Requirements

### Data Requirements

- **Minimal data**: 49 jam data historis berurutan
- **Format timestamp**: ISO 8601 (e.g., "2024-05-01T00:00:00")
- **PM2.5 range**: 0-1000 µg/m³
- **Data harus berurutan**: Tidak boleh ada gap waktu yang besar

### Error Handling

API akan return error jika:
- Data historis kurang dari 49 jam
- PM2.5 density di luar range yang valid
- Format timestamp tidak valid
- Model tidak dapat dimuat

## 🐛 Troubleshooting

### Error: "Model not loaded"
**Solusi**: 
- Pastikan file `aqi_pipeline_enhanced.pkl` ada di root directory
- Jalankan notebook untuk train model

### Error: "Need at least 49 hourly records"
**Solusi**:
- Kirim minimal 49 data points dalam request
- Pastikan data berurutan per jam

### Error: "PM2.5 density seems unreasonably high"
**Solusi**:
- Periksa nilai PM2.5 (harus 0-1000)
- Verifikasi data sensor

### API tidak bisa diakses
**Solusi**:
```bash
# Check if port is already in use
netstat -ano | findstr :8000

# Use different port
uvicorn api.app:app --reload --port 8001
```

## 📝 Model Information

### Features (39 total):
- **Time features**: hour, dayofweek, month, weekofyear, dayofyear (5)
- **Lag features**: aqi_lag_* dan pm25_lag_* untuk 7 lags (14)
- **Rolling features**: aqi_roll_mean_* dan aqi_roll_std_* untuk 5 windows (10)

### Model Architecture:
- **Algorithm**: XGBoost Regressor
- **Regularization**: L1 (alpha=0.5), L2 (lambda=1.5)
- **Hyperparameters**:
  - n_estimators: 1000
  - learning_rate: 0.05
  - max_depth: 3
  - subsample: 0.8
  - colsample_bytree: 0.8

## 📄 License

MIT License

## 👥 Support

Untuk bantuan lebih lanjut:
- Email: support@example.com
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: http://localhost:8000/docs

---

**Version**: 2.0.0  
**Last Updated**: January 2026
- Required signals: `timestamp`, `pm25_density`. Optional: `aqi_ispu` (else derived).
- The API resamples to hourly mean and forward-fills small gaps before feature building.

## Prediction pipeline (server-side)
1) Validate and sort historical records by timestamp.
2) Derive `aqi_ispu` from PM2.5 (ISPU interpolation) if missing.
3) Resample to hourly means, forward-fill gaps, keep the latest 25 hours.
4) Add time features (`hour`, `dayofweek`, `month`), lags, and rolling stats.
5) For each of the 48 steps: create a new row, reuse last PM2.5 (persistence), rebuild features, predict AQI, append to history, repeat.
6) Return the 48 predicted AQI values with timestamps.

## Deployment notes
- Keep `aqi_pipeline.pkl` in the project root (one level above `api/`).
- Use a process manager or container to run `uvicorn`. Example Docker command:
  ```bash
  uvicorn api.app:app --host 0.0.0.0 --port 8000
  ```
- Monitor memory: XGBoost model is light; API uses pandas for feature prep.

## CI/CD checklist for the dev team
- Install deps and run a short contract test (e.g., POST `/predict` with a 25-point fixture and assert 48 outputs).
- Version the model artifact (`aqi_pipeline.pkl`) and pin package versions from `api/requirements.txt`.
- Expose `/health` for liveness probes; add `/predict` latency/error logging.
- If deploying behind TLS/ingress, ensure body size limits allow at least ~10 KB payloads.
