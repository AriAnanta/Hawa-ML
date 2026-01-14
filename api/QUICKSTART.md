# 🚀 Quick Start Guide - AQI Prediction API

Panduan cepat untuk menjalankan API dalam 5 menit!

## ⚡ Quick Setup (5 menit)

### Opsi 1: Menggunakan Python Langsung

```bash
# 1. Install dependencies
pip install -r api/requirements.txt

# 2. Pastikan model tersedia
# Jika belum, jalankan notebook: prediction_AQI_Untuk_API_Enhanced.ipynb

# 3. Run API
uvicorn api.app:app --reload

# 4. Test API
curl http://localhost:8000/health
```

✅ API akan berjalan di: **http://localhost:8000**  
📖 Dokumentasi: **http://localhost:8000/docs**

---

### Opsi 2: Menggunakan Docker

```bash
# 1. Build image
docker build -t aqi-api .

# 2. Run container
docker run -d -p 8000:8000 --name aqi-api aqi-api

# 3. Check logs
docker logs -f aqi-api

# 4. Test API
curl http://localhost:8000/health
```

Atau dengan docker-compose:

```bash
docker-compose up -d
```

---

## 🧪 Testing API

### 1. Health Check

```bash
curl http://localhost:8000/health | python -m json.tool
```

Expected output:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "max_lookback_hours": 49
}
```

### 2. Make Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @api/sample_payload.json
```

### 3. Run Test Script

```bash
python api/test_api.py
```

---

## 📱 Akses Dokumentasi

Setelah API berjalan, buka di browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root Info**: http://localhost:8000/

---

## 🔧 Troubleshooting

### Problem: "Model not found"

```bash
# Solution: Train model menggunakan notebook
jupyter notebook prediction_AQI_Untuk_API_Enhanced.ipynb
# Jalankan semua cells hingga model tersimpan
```

### Problem: "Port already in use"

```bash
# Solution 1: Kill process di port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Solution 2: Gunakan port lain
uvicorn api.app:app --reload --port 8001
```

### Problem: "Import error"

```bash
# Solution: Reinstall dependencies
pip install -r api/requirements.txt --force-reinstall
```

---

## 📚 Next Steps

1. ✅ API sudah berjalan → Baca [README.md](README.md) untuk detail lengkap
2. 🔌 Integrasikan dengan aplikasi → Lihat [EXAMPLES.md](EXAMPLES.md)
3. 🚀 Deploy ke production → Baca [DEPLOYMENT.md](DEPLOYMENT.md)
4. 🧪 Testing lanjutan → Baca [TESTING.md](TESTING.md)

---

## 💡 Tips

- Gunakan `--reload` hanya untuk development
- Untuk production, gunakan multiple workers: `--workers 4`
- Monitor logs untuk debug: `docker logs -f aqi-api`
- Backup model file secara berkala

---

## 📞 Need Help?

- 📖 Dokumentasi: http://localhost:8000/docs
- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**Selamat mencoba! 🎉**
