# Dokumentasi Fitur Prediksi AQI (ISPU) 48 Jam 1

Fitur Prediksi AQI (Air Quality Index) atau ISPU (Indeks Standar Pencemar Udara) adalah komponen cerdas yang menggunakan teknologi **Machine Learning** untuk memprediksi kualitas udara di masa depan berdasarkan data historis.

## 🚀 Fungsi Utama
Komponen ini memberikan wawasan proaktif kepada pengguna mengenai tren kualitas udara selama 48 jam ke depan, sehingga pengguna dapat merencanakan aktivitas luar ruangan dengan lebih aman.

## 🛠️ Cara Kerja Teknis
Fitur ini beroperasi melalui beberapa tahapan integrasi data:

1.  **Pengambilan Data Historis**: Mengambil data kualitas udara (PM2.5) dari backend selama 72 jam terakhir.
2.  **Analisis Machine Learning**: Data tersebut dikirim ke API Machine Learning khusus (`VITE_ML_API_URL`) untuk diproses menggunakan model prediksi.
3.  **Visualisasi Real-time**: Hasil prediksi ditampilkan dalam bentuk grafik garis interaktif dan ringkasan waktu yang mudah dibaca.

## 📊 Fitur Visual & Antarmuka

### 1. Grafik Tren Interaktif
*   **Visualisasi Garis**: Menampilkan naik turunnya nilai AQI selama 48 jam.
*   **Tooltip Detail**: Saat kursor diarahkan ke grafik, muncul informasi spesifik mengenai waktu dan prediksi nilai AQI pada jam tersebut.
*   **Indikator Statistik**: Menampilkan nilai **AQI Saat Ini**, **Rata-rata**, dan **Puncak (Peak)** prediksi.

### 2. Timely Insight (Ringkasan Waktu)
Menampilkan ringkasan kondisi udara pada interval waktu tertentu:
*   **Sekarang (Now)**
*   **+6 Jam** hingga **+48 Jam**
Setiap interval dilengkapi dengan status kualitas udara (Baik, Sedang, Tidak Sehat, dll.) dan kode warna yang sesuai.

### 3. Sistem Kode Warna (Standardisasi)
Warna berubah secara dinamis berdasarkan tingkat polusi:
*   🟢 **Hijau (0-50)**: Baik
*   🟡 **Kuning (51-100)**: Sedang
*   🟠 **Oranye (101-150)**: Tidak Sehat (Sensitif)
*   🔴 **Merah (151-200)**: Tidak Sehat
*   🟣 **Ungu (>200)**: Sangat Tidak Sehat / Berbahaya


## ⚙️ Cara Menjalankan Machine Learning
Untuk mengaktifkan fitur prediksi, Anda perlu menjalankan server ML Python (FastAPI):

1.  **Buka Terminal** dan arahkan ke folder machine learning:
    ```bash
    cd "machine learning/api"
    ```
2.  **Instal Library** yang dibutuhkan (jika belum):
    ```bash
    pip install fastapi uvicorn joblib numpy pandas xgboost pydantic
    ```
3.  **Jalankan Server**:
    ```bash
    uvicorn app_simple:app --host 0.0.0.0 --port 8001 --reload
    ```
    *Server akan berjalan di `http://localhost:8001`*

## � Integrasi API (Frontend)
Frontend melakukan dua tahap pemanggilan API untuk menghasilkan prediksi:

### 1. Mengambil Data Historis (Backend Utama)
Frontend mengambil data PM2.5 dari backend utama sebagai input untuk model ML.
*   **Endpoint**: `/weather/analytics/hourly`
*   **Method**: `GET`
*   **Query Params**: `city={nama_kota}&hours=72`
*   **Headers**: `Authorization: Bearer <token>`

### 2. Melakukan Prediksi (ML API)
Data historis dikirim ke server ML untuk diproses.
*   **Endpoint**: `http://localhost:8001/predict`
*   **Method**: `POST`
*   **Body**: 
    ```json
    [
      { "timestamp": "2024-01-01T00:00:00", "pm25_density": 25.5 },
      ...
    ]
    ```
*   **Output**: Array berisi 48 objek prediksi (timestamp & predicted_aqi).

## �💻 Lokasi File
*   Komponen UI: [AQIPrediction.jsx](file:///c:/Users/user/Downloads/Hawa/hawa-fe-sl2/src/components/AQIPrediction.jsx)
*   Integrasi Dashboard: [Dashboard.jsx](file:///c:/Users/user/Downloads/Hawa/hawa-fe-sl2/src/pages/Dashboard.jsx)
*   Server ML: [app_simple.py](file:///c:/Users/user/Downloads/Hawa/machine%20learning/api/app_simple.py)
