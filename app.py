import sys
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run as app_run

# -----------------------------
# Project imports
# -----------------------------
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from feature_extraction import extract_features   # <-- your advanced extractor

# -----------------------------
# Load model ONCE (VERY IMPORTANT)
# -----------------------------
try:
    preprocessor = load_object("final_model/preprocessor.pkl")
    model = load_object("final_model/model.pkl")

    network_model = NetworkModel(
        preprocessor=preprocessor,
        model=model
    )
    print("✅ Model loaded successfully")

except Exception as e:
    print("❌ Model loading failed:", e)
    sys.exit(1)

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Phishing URL Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Chrome extensions need this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# URL-only input schema
# -----------------------------
class URLInput(BaseModel):
    url: HttpUrl

# -----------------------------
# Prediction endpoint
# -----------------------------
@app.post("/predict")
def predict(payload: URLInput):
    try:
        url = str(payload.url)
        print(url)
        # -----------------------------
        # Extract ALL 30 features here
        # -----------------------------
       
        features = extract_features(url)
        
        # Convert to DataFrame (1 row)
        df = pd.DataFrame([features])
        # Predict
        prediction = network_model.predict(df)[0]
        print(prediction)
        label = "phishing" if prediction == 0 else "legitimate"
        print(label)

        return {
            "url": url,
            "label": label
        }

    except Exception as e:
        return {
            "error": str(e)
        }

# -----------------------------
# Run locally
# -----------------------------
if __name__ == "__main__":
    app_run(app, host="localhost", port=8000)
