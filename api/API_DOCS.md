# API Prediksi AQI - Dokumentasi

API sederhana untuk prediksi Air Quality Index (AQI/ISPU) 48 jam ke depan.

## Instalasi

```bash
pip install fastapi uvicorn pandas numpy xgboost joblib pydantic
```

## Menjalankan API

```bash
uvicorn api.app:app --reload
```

API akan berjalan di: **http://localhost:8000**

## Endpoint

### POST /predict

Memprediksi AQI untuk 48 jam ke depan.

**Request:**
```json
[
  {"timestamp": "2024-05-01T00:00:00", "pm25_density": 18.2},
  {"timestamp": "2024-05-01T01:00:00", "pm25_density": 19.1},
  ...
  (minimal 49 data points)
]
```

**Response:**
```json
{
  "predictions": [
    {
      "timestamp": "2024-05-03T02:00:00",
      "predicted_aqi": 67.45
    },
    {
      "timestamp": "2024-05-03T03:00:00",
      "predicted_aqi": 68.12
    },
    ...
    (48 predictions total)
  ]
}
```

## Cara Menggunakan

### Python
```python
import requests

history = [
    {"timestamp": "2024-05-01T00:00:00", "pm25_density": 22.5},
    # ... 48 data lainnya
]

response = requests.post("http://localhost:8000/predict", json=history)
result = response.json()

for pred in result["predictions"]:
    print(f"{pred['timestamp']}: AQI = {pred['predicted_aqi']}")
```

### cURL
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d @api/sample_payload.json
```

## Dokumentasi Interaktif

Buka di browser: **http://localhost:8000/docs**

## Catatan

- Minimal **49 data historis** per jam diperlukan
- Format timestamp: ISO 8601 (contoh: "2024-05-01T00:00:00")
- PM2.5 dalam satuan µg/m³
- Model: XGBoost dengan recursive forecasting
