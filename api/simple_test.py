"""
Simple test untuk AQI Prediction API
"""

import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

print("🧪 Testing AQI Prediction API\n")

# 1. Test Health Check
print("1️⃣ Testing Health Check...")
try:
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed!")
        data = response.json()
        print(f"   Status: {data['status']}")
        print(f"   Model Type: {data['model_info']['model_type']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Test Prediction
print("\n2️⃣ Testing Prediction...")
try:
    # Generate sample data
    base_time = datetime(2024, 5, 1, 0, 0, 0)
    history = []
    for i in range(50):
        history.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "pm25_density": 20 + (i % 10) * 2.5
        })
    
    response = requests.post(f"{API_URL}/predict", json=history)
    
    if response.status_code == 200:
        print("✅ Prediction successful!")
        result = response.json()
        
        # Print statistics
        stats = result['statistics']
        print(f"\n   📊 Statistics:")
        print(f"      Mean AQI: {stats['mean_aqi']:.2f}")
        print(f"      Min AQI: {stats['min_aqi']:.2f}")
        print(f"      Max AQI: {stats['max_aqi']:.2f}")
        
        # Print first 3 predictions
        print(f"\n   🔮 First 3 Predictions:")
        for i, pred in enumerate(result['forecast'][:3], 1):
            print(f"      {i}. {pred['timestamp']}: {pred['pred_aqi']:.2f} ({pred['category']})")
        
        print(f"\n   ✅ Total predictions: {len(result['forecast'])}")
    else:
        print(f"❌ Prediction failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ Testing complete!")
print("📖 For more details, visit: http://localhost:8000/docs")
print("="*60)
