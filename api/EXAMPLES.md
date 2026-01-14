# 📘 API Usage Examples

Koleksi contoh penggunaan AQI Prediction API dalam berbagai bahasa pemrograman dan tools.

## 📋 Daftar Isi

- [Python](#python)
- [JavaScript](#javascript)
- [cURL](#curl)
- [Postman](#postman)
- [Integration Examples](#integration-examples)

---

## Python

### Basic Usage

```python
import requests
from datetime import datetime, timedelta

# API Configuration
API_URL = "http://localhost:8000"

# Prepare historical data
def generate_history(hours=50):
    base_time = datetime(2024, 5, 1, 0, 0, 0)
    history = []
    
    for i in range(hours):
        history.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "pm25_density": 20 + (i % 10) * 2.5
        })
    
    return history

# Make prediction
history = generate_history()
response = requests.post(f"{API_URL}/predict", json=history)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Prediction successful!")
    print(f"Mean AQI: {result['statistics']['mean_aqi']:.2f}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
```

### Advanced Example with Error Handling

```python
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

class AQIClient:
    """Client for AQI Prediction API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def predict(self, history: List[Dict[str, Any]], simple: bool = False) -> Dict[str, Any]:
        """
        Predict AQI for next 48 hours
        
        Args:
            history: List of historical data points
            simple: Use simple endpoint (without categories)
        
        Returns:
            Prediction results
        """
        endpoint = "/predict/simple" if simple else "/predict"
        
        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=history,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response else str(e)
            raise Exception(f"API Error: {error_detail}")
        
        except requests.exceptions.Timeout:
            raise Exception("Request timeout - API took too long to respond")
        
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to API at {self.base_url}")
    
    def predict_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict from pandas DataFrame
        
        Args:
            df: DataFrame with 'timestamp' and 'pm25_density' columns
        
        Returns:
            Prediction results
        """
        # Validate columns
        required_cols = ['timestamp', 'pm25_density']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Convert to list of dicts
        history = df[required_cols].to_dict('records')
        
        # Convert timestamps to ISO format if needed
        for item in history:
            if isinstance(item['timestamp'], pd.Timestamp):
                item['timestamp'] = item['timestamp'].isoformat()
        
        return self.predict(history)
    
    def get_forecast_dataframe(self, prediction_result: Dict[str, Any]) -> pd.DataFrame:
        """Convert prediction result to DataFrame"""
        forecast_data = prediction_result['forecast']
        df = pd.DataFrame(forecast_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df


# Example Usage
if __name__ == "__main__":
    # Initialize client
    client = AQIClient("http://localhost:8000")
    
    # Check health
    try:
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"   Model: {health['model_info']['model_type']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        exit(1)
    
    # Generate sample data
    base_time = datetime(2024, 5, 1, 0, 0, 0)
    history = []
    for i in range(50):
        history.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "pm25_density": 25 + (i % 15) * 1.8
        })
    
    # Make prediction
    try:
        result = client.predict(history)
        
        # Print statistics
        print("\n📊 Prediction Statistics:")
        for key, value in result['statistics'].items():
            print(f"   {key}: {value:.2f}")
        
        # Convert to DataFrame
        df = client.get_forecast_dataframe(result)
        print(f"\n📈 Forecast DataFrame (first 5 rows):")
        print(df.head())
        
        # Save to CSV
        df.to_csv("aqi_forecast.csv", index=False)
        print(f"\n💾 Forecast saved to aqi_forecast.csv")
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
```

### Load from CSV and Predict

```python
import pandas as pd
import requests

# Load historical data from CSV
df = pd.read_csv("synthetic_iot_data.csv")
df['timestamp'] = pd.to_datetime(df['Timestamp'])
df = df.rename(columns={'PM2.5 density': 'pm25_density'})

# Select last 50 hours
df_recent = df.tail(50)[['timestamp', 'pm25_density']]

# Convert to list of dicts
history = df_recent.to_dict('records')

# Convert timestamps to ISO format
for item in history:
    item['timestamp'] = item['timestamp'].isoformat()

# Make prediction
response = requests.post("http://localhost:8000/predict", json=history)
result = response.json()

# Convert forecast to DataFrame
forecast_df = pd.DataFrame(result['forecast'])
forecast_df['timestamp'] = pd.to_datetime(forecast_df['timestamp'])

# Plot
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))
plt.plot(df_recent['timestamp'], df_recent['pm25_density'], label='Historical PM2.5', marker='o')
plt.plot(forecast_df['timestamp'], forecast_df['pred_aqi'], label='Predicted AQI', linestyle='--', marker='s')
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('PM2.5 History and AQI Forecast')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('aqi_forecast_plot.png', dpi=300)
plt.show()
```

---

## JavaScript

### Using fetch (Browser/Node.js)

```javascript
// API Configuration
const API_URL = 'http://localhost:8000';

// Generate sample history
function generateHistory(hours = 50) {
  const baseTime = new Date('2024-05-01T00:00:00');
  const history = [];
  
  for (let i = 0; i < hours; i++) {
    const timestamp = new Date(baseTime.getTime() + i * 3600000);
    history.push({
      timestamp: timestamp.toISOString(),
      pm25_density: 20 + (i % 10) * 2.5
    });
  }
  
  return history;
}

// Make prediction
async function predictAQI() {
  try {
    const history = generateHistory();
    
    const response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(history)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    console.log('✅ Prediction successful!');
    console.log(`Mean AQI: ${result.statistics.mean_aqi.toFixed(2)}`);
    console.log(`Min AQI: ${result.statistics.min_aqi.toFixed(2)}`);
    console.log(`Max AQI: ${result.statistics.max_aqi.toFixed(2)}`);
    
    return result;
    
  } catch (error) {
    console.error('❌ Prediction failed:', error);
    throw error;
  }
}

// Health check
async function checkHealth() {
  try {
    const response = await fetch(`${API_URL}/health`);
    const health = await response.json();
    console.log('API Status:', health.status);
    return health;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
}

// Run
checkHealth().then(() => predictAQI());
```

### Using axios

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Predict AQI
async function predictAQI(history) {
  try {
    const response = await apiClient.post('/predict', history);
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error
      console.error('Server error:', error.response.data);
      throw new Error(error.response.data.detail);
    } else if (error.request) {
      // No response received
      throw new Error('No response from server');
    } else {
      throw new Error(error.message);
    }
  }
}

// Example usage
(async () => {
  // Generate history
  const history = Array.from({ length: 50 }, (_, i) => ({
    timestamp: new Date(Date.now() - (50 - i) * 3600000).toISOString(),
    pm25_density: 20 + (i % 10) * 2.5
  }));
  
  // Make prediction
  const result = await predictAQI(history);
  console.log('Statistics:', result.statistics);
  console.log('First 3 predictions:', result.forecast.slice(0, 3));
})();
```

### React Integration

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AQIPredictor = () => {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const API_URL = 'http://localhost:8000';
  
  const predictAQI = async (history) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_URL}/predict`, history);
      setForecast(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="aqi-predictor">
      <h1>AQI Prediction</h1>
      
      {loading && <p>Loading...</p>}
      {error && <p className="error">Error: {error}</p>}
      
      {forecast && (
        <div className="forecast-results">
          <h2>Statistics</h2>
          <ul>
            <li>Mean AQI: {forecast.statistics.mean_aqi.toFixed(2)}</li>
            <li>Min AQI: {forecast.statistics.min_aqi.toFixed(2)}</li>
            <li>Max AQI: {forecast.statistics.max_aqi.toFixed(2)}</li>
          </ul>
          
          <h2>Forecast (First 5 Hours)</h2>
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>AQI</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {forecast.forecast.slice(0, 5).map((pred, idx) => (
                <tr key={idx}>
                  <td>{new Date(pred.timestamp).toLocaleString()}</td>
                  <td>{pred.pred_aqi.toFixed(2)}</td>
                  <td>{pred.category}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AQIPredictor;
```

---

## cURL

### Health Check

```bash
curl -X GET "http://localhost:8000/health" | json_pp
```

### Simple Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d @api/sample_payload.json
```

### Prediction with Custom Data

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp": "2024-05-01T00:00:00", "pm25_density": 22.5},
    {"timestamp": "2024-05-01T01:00:00", "pm25_density": 24.1}
  ]' | json_pp
```

### Save Response to File

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d @api/sample_payload.json \
  -o forecast_result.json
```

---

## Postman

### Import Collection

1. Create new collection: "AQI Prediction API"
2. Add requests:

#### Request 1: Health Check
- **Method**: GET
- **URL**: `{{baseUrl}}/health`
- **Tests**:
```javascript
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Model is loaded", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.model_loaded).to.be.true;
});
```

#### Request 2: Predict AQI
- **Method**: POST
- **URL**: `{{baseUrl}}/predict`
- **Body**: Raw (JSON)
```json
[
  {"timestamp": "2024-05-01T00:00:00", "pm25_density": 22.5},
  ...
]
```
- **Tests**:
```javascript
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Has 48 predictions", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.forecast).to.have.lengthOf(48);
});

pm.test("All predictions have category", function () {
    var jsonData = pm.response.json();
    jsonData.forecast.forEach(pred => {
        pm.expect(pred).to.have.property('category');
    });
});
```

### Environment Variables
- `baseUrl`: `http://localhost:8000`

---

## Integration Examples

### Flask Integration

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
AQI_API_URL = "http://localhost:8000"

@app.route('/get-forecast', methods=['POST'])
def get_forecast():
    """Proxy endpoint to AQI API"""
    try:
        # Get history from request
        history = request.json
        
        # Call AQI API
        response = requests.post(
            f"{AQI_API_URL}/predict",
            json=history,
            timeout=30
        )
        response.raise_for_status()
        
        return jsonify(response.json())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json

AQI_API_URL = "http://localhost:8000"

@csrf_exempt
def predict_aqi(request):
    if request.method == 'POST':
        try:
            history = json.loads(request.body)
            
            response = requests.post(
                f"{AQI_API_URL}/predict",
                json=history,
                timeout=30
            )
            response.raise_for_status()
            
            return JsonResponse(response.json())
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
```

---

## Tips & Best Practices

1. **Retry Logic**: Implement retry for failed requests
2. **Caching**: Cache predictions to reduce API calls
3. **Batching**: Group multiple requests if possible
4. **Error Handling**: Always handle network errors gracefully
5. **Timeouts**: Set appropriate timeout values
6. **Rate Limiting**: Implement rate limiting on client side

---

**Last Updated**: January 2026
