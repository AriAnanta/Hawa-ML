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
- **Deskripsi**: Menerima data historis (bisa data mentah per 30 detik atau per menit). Server akan otomatis melakukan **resampling ke rata-rata per jam** sebelum melakukan prediksi. Dibutuhkan minimal rentang data 24 jam.

## Contoh Input Data (JSON)

### 1. Data per Jam (Standard)
Berikut adalah contoh data **24 jam lengkap** (satu data per jam). Minimal dibutuhkan 24 data per jam untuk hasil yang akurat.

```json
{
  "history": [
    {"timestamp": "2025-12-05 00:00:00", "PM2.5_ug_m3": 25.5, "PM10_ug_m3": 35.2},
    ...
    {"timestamp": "2025-12-05 23:00:00", "PM2.5_ug_m3": 30.1, "PM10_ug_m3": 42.5}
  ]
}
```

### 2. Data IoT (Interval 30 Detik)
API ini mendukung pengiriman data mentah langsung dari IoT (misal setiap 30 detik). Server akan otomatis merata-ratakan data tersebut ke dalam interval 1 jam. Pastikan total rentang waktu data yang dikirim mencakup minimal 24 jam.

```json
{
  "history": [
    {"timestamp": "2025-12-05 22:08:36", "PM2.5_ug_m3": 6.5, "PM10_ug_m3": 8.4},
    {"timestamp": "2025-12-05 22:09:10", "PM2.5_ug_m3": 5.6, "PM10_ug_m3": 7.3},
    {"timestamp": "2025-12-05 22:09:40", "PM2.5_ug_m3": 5.8, "PM10_ug_m3": 7.5},
    {"timestamp": "2025-12-05 22:10:10", "PM2.5_ug_m3": 6.1, "PM10_ug_m3": 7.9},
    {"timestamp": "2025-12-05 22:10:40", "PM2.5_ug_m3": 6.3, "PM10_ug_m3": 8.1}
  ]
}
```
*Catatan: Contoh di atas hanya cuplikan. Untuk prediksi yang valid, kirimkan data yang mencakup rentang waktu minimal 24 jam (sekitar 2880 data jika intervalnya 30 detik).*

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
