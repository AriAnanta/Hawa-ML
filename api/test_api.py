"""
Test script for AQI Prediction API
Run this script to test the API endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# API Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def print_section(title):
    """Print formatted section title"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_root():
    """Test root endpoint"""
    print_section("Testing Root Endpoint (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_health():
    """Test health check endpoint"""
    print_section("Testing Health Check (GET /health)")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_sample_data(hours=50):
    """Generate sample historical data"""
    base_time = datetime(2024, 5, 1, 0, 0, 0)
    history = []
    
    for i in range(hours):
        # Simulate PM2.5 data with some variation
        pm25 = 20 + (i % 20) * 1.5 + (i % 5) * 0.5
        
        history.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "pm25_density": round(pm25, 2)
        })
    
    return history


def test_predict_full():
    """Test full prediction endpoint"""
    print_section("Testing Full Prediction (POST /predict)")
    
    try:
        # Generate sample data
        history = generate_sample_data(50)
        print(f"Generated {len(history)} data points")
        print(f"First data point: {history[0]}")
        print(f"Last data point: {history[-1]}")
        
        # Make prediction request
        response = requests.post(
            f"{BASE_URL}/predict",
            headers=HEADERS,
            json=history
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📊 Statistics:")
            for key, value in result['statistics'].items():
                print(f"  {key}: {value:.2f}")
            
            print("\n📋 Metadata:")
            for key, value in result['metadata'].items():
                if key != 'prediction_time':
                    print(f"  {key}: {value}")
            
            print("\n🔮 First 5 Predictions:")
            for i, pred in enumerate(result['forecast'][:5], 1):
                print(f"  {i}. {pred['timestamp']}: {pred['pred_aqi']:.2f} - {pred['category']}")
            
            print(f"\n✅ Total predictions: {len(result['forecast'])}")
            return True
        else:
            print(f"❌ Error Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_predict_simple():
    """Test simple prediction endpoint"""
    print_section("Testing Simple Prediction (POST /predict/simple)")
    
    try:
        history = generate_sample_data(50)
        
        response = requests.post(
            f"{BASE_URL}/predict/simple",
            headers=HEADERS,
            json=history
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Total predictions: {len(result['forecast'])}")
            print("\n🔮 First 3 Predictions:")
            for i, pred in enumerate(result['forecast'][:3], 1):
                print(f"  {i}. {pred['timestamp']}: {pred['pred_aqi']:.2f}")
            return True
        else:
            print(f"❌ Error Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_handling():
    """Test error handling with insufficient data"""
    print_section("Testing Error Handling (Insufficient Data)")
    
    try:
        # Only 10 data points (should fail - need 49)
        history = generate_sample_data(10)
        
        response = requests.post(
            f"{BASE_URL}/predict",
            headers=HEADERS,
            json=history
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 400 error
        return response.status_code == 400
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_pm25():
    """Test error handling with invalid PM2.5 values"""
    print_section("Testing Error Handling (Invalid PM2.5)")
    
    try:
        history = generate_sample_data(50)
        # Set invalid PM2.5 value
        history[0]["pm25_density"] = -10  # Negative value
        
        response = requests.post(
            f"{BASE_URL}/predict",
            headers=HEADERS,
            json=history
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 422 (validation error)
        return response.status_code == 422
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 "*20)
    print("     AQI PREDICTION API - TEST SUITE")
    print("🧪 "*20)
    
    print(f"\n🌐 Testing API at: {BASE_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if API is running
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API!")
        print(f"   Make sure the API is running at {BASE_URL}")
        print("   Run: uvicorn api.app:app --reload")
        sys.exit(1)
    
    # Run tests
    results = {
        "Root Endpoint": test_root(),
        "Health Check": test_health(),
        "Full Prediction": test_predict_full(),
        "Simple Prediction": test_predict_simple(),
        "Error Handling (Insufficient Data)": test_error_handling(),
        "Error Handling (Invalid PM2.5)": test_invalid_pm25()
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"{'='*60}\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
