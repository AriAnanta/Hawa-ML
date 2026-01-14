# 🚀 Deployment Guide - AQI Prediction API

Panduan lengkap untuk deploy API ke berbagai platform.

## 📋 Daftar Isi

- [Persiapan Deployment](#persiapan-deployment)
- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
  - [Heroku](#heroku)
  - [Azure App Service](#azure-app-service)
  - [AWS EC2](#aws-ec2)
  - [Google Cloud Run](#google-cloud-run)
- [Performance Tuning](#performance-tuning)
- [Monitoring](#monitoring)

---

## Persiapan Deployment

### 1. Checklist Sebelum Deploy

- [ ] Model `aqi_pipeline_enhanced.pkl` sudah dilatih dan tersedia
- [ ] Semua dependencies terinstall (`requirements.txt`)
- [ ] API sudah ditest di local (gunakan `test_api.py`)
- [ ] Environment variables sudah dikonfigurasi
- [ ] CORS settings sesuai dengan frontend domain

### 2. Verifikasi Model

```bash
# Pastikan file model ada
ls -lh aqi_pipeline_enhanced.pkl

# Test load model
python -c "import joblib; print(joblib.load('aqi_pipeline_enhanced.pkl').keys())"
```

---

## Local Deployment

### Development Server

```bash
# Basic
uvicorn api.app:app --reload

# With custom host and port
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# With log level
uvicorn api.app:app --reload --log-level info
```

### Production Server (Local)

```bash
# Multiple workers
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn (recommended for production)
pip install gunicorn
gunicorn api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Docker Deployment

### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY aqi_pipeline_enhanced.pkl .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.venv
venv/
*.ipynb
.git
.gitignore
README.md
```

### 3. Build and Run

```bash
# Build image
docker build -t aqi-prediction-api:latest .

# Run container
docker run -d -p 8000:8000 --name aqi-api aqi-prediction-api:latest

# Check logs
docker logs -f aqi-api

# Stop container
docker stop aqi-api
```

### 4. Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

---

## Cloud Deployment

### Heroku

#### 1. Create Procfile

```
web: uvicorn api.app:app --host 0.0.0.0 --port $PORT
```

#### 2. Create runtime.txt

```
python-3.10.12
```

#### 3. Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create aqi-prediction-api

# Add buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Open app
heroku open
```

---

### Azure App Service

#### 1. Install Azure CLI

```bash
# Windows
winget install Microsoft.AzureCLI

# Linux/Mac
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 2. Deploy

```bash
# Login
az login

# Create resource group
az group create --name aqi-api-rg --location eastus

# Create App Service plan
az appservice plan create --name aqi-api-plan --resource-group aqi-api-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group aqi-api-rg --plan aqi-api-plan --name aqi-prediction-api --runtime "PYTHON|3.10"

# Configure startup command
az webapp config set --resource-group aqi-api-rg --name aqi-prediction-api --startup-file "uvicorn api.app:app --host 0.0.0.0 --port 8000"

# Deploy code
az webapp up --name aqi-prediction-api --resource-group aqi-api-rg
```

---

### AWS EC2

#### 1. Launch EC2 Instance

- AMI: Ubuntu Server 22.04 LTS
- Instance Type: t2.small atau lebih besar
- Security Group: Allow port 8000 (atau 80/443)

#### 2. Setup Server

```bash
# SSH ke instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-venv -y

# Clone repository
git clone <your-repo-url>
cd ai-sl2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt

# Install supervisor untuk process management
sudo apt install supervisor -y
```

#### 3. Create Supervisor Config

Create `/etc/supervisor/conf.d/aqi-api.conf`:

```ini
[program:aqi-api]
command=/home/ubuntu/ai-sl2/venv/bin/uvicorn api.app:app --host 0.0.0.0 --port 8000
directory=/home/ubuntu/ai-sl2
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/aqi-api/err.log
stdout_logfile=/var/log/aqi-api/out.log
```

#### 4. Start Service

```bash
# Create log directory
sudo mkdir -p /var/log/aqi-api
sudo chown ubuntu:ubuntu /var/log/aqi-api

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start aqi-api

# Check status
sudo supervisorctl status aqi-api
```

#### 5. Setup Nginx (Optional)

```bash
# Install nginx
sudo apt install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/aqi-api
```

Config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/aqi-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Google Cloud Run

#### 1. Install gcloud CLI

```bash
# Follow: https://cloud.google.com/sdk/docs/install
gcloud init
```

#### 2. Build and Deploy

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aqi-api

# Deploy to Cloud Run
gcloud run deploy aqi-api \
  --image gcr.io/YOUR_PROJECT_ID/aqi-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1
```

---

## Performance Tuning

### 1. Workers Configuration

```bash
# Recommended formula: (2 x CPU cores) + 1
# For 4 cores:
uvicorn api.app:app --workers 9
```

### 2. Gunicorn + Uvicorn Workers

```bash
gunicorn api.app:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5
```

### 3. Environment Variables

Create `.env` file:
```
LOG_LEVEL=info
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
```

### 4. Caching (Optional)

Consider adding Redis for caching predictions:

```python
# In app.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="aqi-cache")
```

---

## Monitoring

### 1. Health Check Endpoint

API sudah memiliki `/health` endpoint. Monitor dengan:

```bash
# Curl
curl http://your-api-url/health

# Watch (every 30s)
watch -n 30 curl http://your-api-url/health
```

### 2. Logging

Enable detailed logging:

```python
# In app.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
```

### 3. Monitoring Tools

- **Prometheus + Grafana**: For metrics
- **Sentry**: For error tracking
- **New Relic / DataDog**: Application monitoring
- **Uptime Robot**: Uptime monitoring

### 4. Setup Prometheus (Example)

```bash
pip install prometheus-fastapi-instrumentator
```

In `app.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
```

---

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Restrict CORS origins
- [ ] Add API rate limiting
- [ ] Implement authentication if needed
- [ ] Keep dependencies updated
- [ ] Don't expose sensitive errors in production
- [ ] Use environment variables for sensitive data
- [ ] Regular security audits

---

## Troubleshooting

### Issue: Model file too large for Git

Solution: Use Git LFS
```bash
git lfs install
git lfs track "*.pkl"
git add .gitattributes
```

### Issue: Out of memory

Solution: Increase instance memory or optimize model
```bash
# Check memory usage
free -h

# Monitor in real-time
htop
```

### Issue: Slow predictions

Solution:
1. Use model quantization
2. Add caching layer
3. Increase worker count
4. Use faster instance type

---

## Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Last Updated**: January 2026
