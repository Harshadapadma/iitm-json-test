from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Resolve file path relative to app.py
root = Path(__file__).parent
json_file = root / "q-vercel-latency.json"

# Load telemetry JSON once at startup
with open(json_file) as f:
    telemetry = pd.DataFrame(json.load(f))

@app.post("/")
async def latency_metrics(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    result = {}

    for region in regions:
        df_region = telemetry[telemetry["region"] == region]
        if df_region.empty:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        avg_latency = df_region["latency_ms"].mean()
        p95_latency = np.percentile(df_region["latency_ms"], 95)
        avg_uptime = df_region["uptime"].mean()
        breaches = (df_region["latency_ms"] > threshold).sum()

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": int(breaches)
        }

    return result
