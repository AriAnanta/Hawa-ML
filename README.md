# Hawa ISPU Prediction API

API ini digunakan untuk memprediksi Indeks Standar Pencemar Udara (ISPU) berdasarkan data historis sensor IoT. API ini menggunakan model ElasticNet yang telah dilatih dan diekspor ke format JSON agar ringan (tanpa dependensi `scikit-learn`).

## Endpoint Utama

### 1. Cek Status
- **URL**: `/`
- **Method**: `GET`
- **Deskripsi**: Mengecek apakah API sedang aktif dan melihat versi model.

### 2. Prediksi & Forecast 48 Jam
- **URL**: `/predict`
- **Method**: `POST`
- **Deskripsi**: Menerima data historis 24 jam terakhir (PM2.5 & PM10) dan mengembalikan prediksi ISPU untuk jam berikutnya serta estimasi forecast untuk 48 jam ke depan. Nilai ISPU akan dihitung secara otomatis jika tidak disediakan.

## Contoh Input Data (JSON)

API membutuhkan minimal **24 data historis** (24 jam) untuk menghitung fitur *rolling statistics*. Berikut adalah contoh data yang bisa Anda gunakan (nilai `aqi_ispu` sekarang opsional karena dihitung otomatis oleh server):

```json
{
  "history": [
    {"timestamp": "2024-07-03T00:00:00", "PM2.5_ug_m3": 25.5, "PM10_ug_m3": 40.2},
    {"timestamp": "2024-07-03T01:00:00", "PM2.5_ug_m3": 26.1, "PM10_ug_m3": 41.0},
    {"timestamp": "2024-07-03T02:00:00", "PM2.5_ug_m3": 24.8, "PM10_ug_m3": 39.5},
    {"timestamp": "2024-07-03T03:00:00", "PM2.5_ug_m3": 23.2, "PM10_ug_m3": 38.0},
    {"timestamp": "2024-07-03T04:00:00", "PM2.5_ug_m3": 22.5, "PM10_ug_m3": 37.2},
    {"timestamp": "2024-07-03T05:00:00", "PM2.5_ug_m3": 21.0, "PM10_ug_m3": 36.5},
    {"timestamp": "2024-07-03T06:00:00", "PM2.5_ug_m3": 28.5, "PM10_ug_m3": 42.0},
    {"timestamp": "2024-07-03T07:00:00", "PM2.5_ug_m3": 35.2, "PM10_ug_m3": 48.5},
    {"timestamp": "2024-07-03T08:00:00", "PM2.5_ug_m3": 38.0, "PM10_ug_m3": 52.1},
    {"timestamp": "2024-07-03T09:00:00", "PM2.5_ug_m3": 40.5, "PM10_ug_m3": 55.0},
    {"timestamp": "2024-07-03T10:00:00", "PM2.5_ug_m3": 42.1, "PM10_ug_m3": 58.2},
    {"timestamp": "2024-07-03T11:00:00", "PM2.5_ug_m3": 39.5, "PM10_ug_m3": 56.0},
    {"timestamp": "2024-07-03T12:00:00", "PM2.5_ug_m3": 37.0, "PM10_ug_m3": 53.5},
    {"timestamp": "2024-07-03T13:00:00", "PM2.5_ug_m3": 35.5, "PM10_ug_m3": 51.2},
    {"timestamp": "2024-07-03T14:00:00", "PM2.5_ug_m3": 34.2, "PM10_ug_m3": 50.0},
    {"timestamp": "2024-07-03T15:00:00", "PM2.5_ug_m3": 33.0, "PM10_ug_m3": 49.2},
    {"timestamp": "2024-07-03T16:00:00", "PM2.5_ug_m3": 36.5, "PM10_ug_m3": 52.5},
    {"timestamp": "2024-07-03T17:00:00", "PM2.5_ug_m3": 45.0, "PM10_ug_m3": 62.1},
    {"timestamp": "2024-07-03T18:00:00", "PM2.5_ug_m3": 48.2, "PM10_ug_m3": 65.5},
    {"timestamp": "2024-07-03T19:00:00", "PM2.5_ug_m3": 50.5, "PM10_ug_m3": 68.2},
    {"timestamp": "2024-07-03T20:00:00", "PM2.5_ug_m3": 45.1, "PM10_ug_m3": 62.5},
    {"timestamp": "2024-07-03T21:00:00", "PM2.5_ug_m3": 40.2, "PM10_ug_m3": 58.0},
    {"timestamp": "2024-07-03T22:00:00", "PM2.5_ug_m3": 35.5, "PM10_ug_m3": 52.5},
    {"timestamp": "2024-07-03T23:00:00", "PM2.5_ug_m3": 30.2, "PM10_ug_m3": 45.5}
  ]
}
```

## Contoh Output Data

```json
{
  "success": true,
  "prediction": 63.45,
  "forecast_48h": [
    {
      "hour": 1,
      "timestamp": "2024-07-04T00:00:00",
      "predicted_aqi": 63.45
    },
    {
      "hour": 2,
      "timestamp": "2024-07-04T01:00:00",
      "predicted_aqi": 64.82
    },
    ...
    {
      "hour": 48,
      "timestamp": "2024-07-05T23:00:00",
      "predicted_aqi": 70.12
    }
  ],
  "model_info": {
    "type": "ElasticNet",
    "features_used": 147
  }
}
```

## Cara Menjalankan Secara Lokal

1. Pastikan Python sudah terinstal.
2. Instal dependensi:
   ```bash
   pip install fastapi uvicorn pandas numpy
   ```
3. Jalankan server:
   ```bash
   python ml/app_ispu.py
   ```
4. Akses di: `http://localhost:8005/docs`
