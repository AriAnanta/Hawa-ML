# Panduan Deploy ML Model ke Vercel

## Masalah
Deployment gagal karena ukuran file melebihi 300MB limit Vercel (314MB).

## Solusi yang Diimplementasikan

### 1. Upload Model ke Cloud Storage
Karena file `.pkl` tidak bisa di-deploy langsung ke Vercel, upload model Anda ke salah satu platform berikut:

#### Option A: GitHub Release (Recommended)
1. Buat release baru di GitHub repository Anda
2. Upload kedua file model:
   - `pm25_pipeline_enhanced.pkl`
   - `pm10_pipeline_enhanced.pkl`
3. Copy URL download untuk setiap file (klik kanan > Copy link address)

#### Option B: Google Drive
1. Upload file ke Google Drive
2. Set sharing ke "Anyone with the link"
3. Gunakan direct download link format:
   ```
   https://drive.google.com/uc?export=download&id=FILE_ID
   ```

#### Option C: Dropbox
1. Upload file ke Dropbox
2. Ganti `dl=0` dengan `dl=1` di URL untuk direct download

### 2. Set Environment Variables di Vercel
1. Buka project Vercel Anda
2. Go to Settings > Environment Variables
3. Tambahkan 2 environment variables:
   - `PM25_MODEL_URL`: URL download untuk `pm25_pipeline_enhanced.pkl`
   - `PM10_MODEL_URL`: URL download untuk `pm10_pipeline_enhanced.pkl`

### 3. Deploy
Setelah environment variables di-set, push code ke GitHub dan Vercel akan auto-deploy.

Model akan otomatis di-download saat pertama kali API dipanggil.

## Alternative: Gunakan Vercel Blob Storage

Jika ingin menggunakan Vercel Blob Storage (berbayar):
```bash
npm i -g vercel
vercel blob upload pm25_pipeline_enhanced.pkl --token YOUR_TOKEN
vercel blob upload pm10_pipeline_enhanced.pkl --token YOUR_TOKEN
```

## Testing Lokal
```bash
# Set environment variables
$env:PM25_MODEL_URL="YOUR_PM25_URL"
$env:PM10_MODEL_URL="YOUR_PM10_URL"

# Run
python -m uvicorn app_simple:app --reload
```
