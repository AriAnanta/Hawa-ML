# Testing the AQI Forecast API

## Prerequisites
- Python environment with dependencies: `pip install -r api/requirements.txt`
- Model artifact present at `aqi_pipeline.pkl` (project root).
- API running locally:
  ```bash
  uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
  ```

## Quick Postman test
1. Open Postman, create a new `POST` request to `http://localhost:8000/predict`.
2. Set `Headers`: `Content-Type: application/json`.
3. Body: `raw` -> `JSON` -> paste contents of `api/sample_payload.json`.
4. Send. You should receive 48 forecasted points with timestamps and metadata.

## cURL alternative
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  --data @api/sample_payload.json
```

## Expected response shape
```json
{
  "forecast": [
    {"timestamp": "2024-05-02T01:00:00", "pred_aqi": 87.4},
    {"timestamp": "2024-05-02T02:00:00", "pred_aqi": 90.1}
  ],
  "metadata": {
    "horizon_hours": 48,
    "required_history_hours": 25,
    "features_used": ["hour", "dayofweek", "month", "aqi_lag_1", ...]
  }
}
```

## Notes
- The sample payload contains 25 consecutive hourly PM2.5 readings (minimum required).
- `aqi_ispu` is optional; the API derives it from PM2.5 if absent.
- If you see a 400 error about history length, ensure you kept all 25 rows and timestamps are valid ISO 8601.
- For other environments, replace `localhost:8000` with your deployed host.
