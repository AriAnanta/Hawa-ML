# Dokumentasi Fitur Prediksi AQI (ISPU) 48 Jam (PM2.5 & PM10)

Fitur Prediksi AQI (Air Quality Index) atau ISPU (Indeks Standar Pencemar Udara) adalah komponen cerdas yang menggunakan teknologi **Machine Learning** untuk memprediksi kualitas udara di masa depan berdasarkan data historis. Sistem ini mendukung prediksi untuk dua jenis polutan utama: **PM2.5** dan **PM10**.

## 🚀 Fungsi Utama
Komponen ini memberikan wawasan proaktif kepada pengguna mengenai tren kualitas udara selama 48 jam ke depan, sehingga pengguna dapat merencanakan aktivitas luar ruangan dengan lebih aman. Model telah dioptimalkan secara terpisah untuk karakteristik penyebaran partikel PM2.5 dan PM10.

## 🛠️ Cara Kerja Teknis
Fitur ini beroperasi melalui beberapa tahapan integrasi data:

1.  **Pengambilan Data Historis**: Mengambil data kualitas udara (PM2.5 atau PM10) dari backend selama 72 jam terakhir.
2.  **Analisis Machine Learning**: Data dikirim ke API Machine Learning (`app_simple.py`) yang secara dinamis memuat model yang sesuai (`.pkl`) berdasarkan jenis polutan yang diminta.
3.  **Feature Engineering**: API menghitung *lag features* dan *rolling averages* secara real-time sebelum melakukan inferensi.
4.  **Visualisasi Real-time**: Hasil prediksi ditampilkan dalam bentuk grafik garis interaktif dan ringkasan waktu.

## 📊 Fitur Visual & Antarmuka
- **Grafik Tren Interaktif**: Menampilkan naik turunnya nilai AQI selama 48 jam.
- **Timely Insight**: Ringkasan kondisi udara (Sekarang, +6 Jam, dst.) dengan status kualitas udara.
- **Sistem Kode Warna**: 
  - 🟢 **Baik (0-50)**
  - 🟡 **Sedang (51-100)**
  - 🟠 **Tidak Sehat (Sensitif) (101-150)**
  - 🔴 **Tidak Sehat (151-200)**
  - 🟣 **Sangat Tidak Sehat / Berbahaya (>200)**

## ⚙️ Cara Menjalankan Secara Lokal
Untuk mengaktifkan fitur prediksi di komputer lokal:

1.  **Arahkan ke folder machine learning**:
    ```bash
    cd "machine learning"
    ```
2.  **Instal Library** yang dibutuhkan:
    ```bash
    pip install fastapi uvicorn joblib numpy pandas xgboost pydantic
    ```
3.  **Jalankan Server**:
    ```bash
    python app_simple.py
    ```
    *Server akan berjalan di `http://localhost:8001`*

## 🌐 Deployment ke Vercel
Untuk men-deploy API Machine Learning ini ke Vercel agar dapat diakses secara publik:

### 1. Persiapan File
Pastikan file berikut ada di root folder `machine learning/`:
- `app_simple.py` (File utama FastAPI)
- `pm25_pipeline_enhanced.pkl` & `pm10_pipeline_enhanced.pkl` (Model yang sudah dilatih)
- `requirements.txt` (Daftar library)
- `vercel.json` (Konfigurasi deployment)

### 2. Isi `vercel.json`
Buat file `vercel.json` dengan isi:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/app_simple.py" }
  ]
}
```

### 3. Langkah Deployment
1. Install Vercel CLI: `npm install -g vercel`
2. Jalankan perintah `vercel` di dalam folder `machine learning`.
3. Ikuti instruksi di terminal (pilih "Yes" untuk semua default).
4. Setelah selesai, Anda akan mendapatkan URL publik (misal: `https://hawa-ml-api.vercel.app`).

## 🔌 Integrasi API
API menerima request POST dengan struktur berikut:

*   **Endpoint**: `/predict`
*   **Method**: `POST`
*   **Payload**:
    ```json
    {
      "pollutant": "pm25",
      "history": [
        { "timestamp": "2024-01-01T00:00:00", "pm25_density": 25.5, "pm10_density": 40.2 },
        ...
      ]
    }
    ```
*   **Output**: Array berisi 48 objek prediksi (`timestamp` & `predicted_aqi`).

## � Lokasi File Utama
*   **API Server**: [app_simple.py](file:///c:/Users/user/Downloads/Hawa/machine%20learning/app_simple.py)
*   **Model PM2.5**: [pm25_pipeline_enhanced.pkl](file:///c:/Users/user/Downloads/Hawa/machine%20learning/pm25_pipeline_enhanced.pkl)
*   **Model PM10**: [pm10_pipeline_enhanced.pkl](file:///c:/Users/user/Downloads/Hawa/machine%20learning/pm10_pipeline_enhanced.pkl)
