# app.py
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import time
import json
from joblib import load
import numpy as np
from typing import Optional

# OpenTelemetry imports - optional. If CloudTrace exporter isn't present we keep running.
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    _cloud_trace_available = True
except Exception:
    _cloud_trace_available = False

# Setup Tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

if _cloud_trace_available:
    span_processor = BatchSpanProcessor(CloudTraceSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)
else:
    # If CloudTrace exporter isn't available, still set up a no-op processor.
    # (You can add other exporters here.)
    pass

# Setup structured logging (JSON-like)
logger = logging.getLogger("iris-ml-service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

formatter = logging.Formatter(json.dumps({
    "severity": "%(levelname)s",
    "message": "%(message)s",
    "timestamp": "%(asctime)s"
}))
handler.setFormatter(formatter)
logger.addHandler(handler)

# FastAPI app
app = FastAPI()

# App state flags
app_state = {"is_ready": False, "is_alive": True}

# Path to your model file
MODEL_PATH = "model-v1.joblib"

# Pydantic schema for incoming Iris data
class IrisData(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.on_event("startup")
async def startup_event():
    """
    Load the real model during startup so readiness probe remains False
    until model is loaded.
    """
    try:
        # load model (this is blocking but OK in startup)
        app.state.model = load(MODEL_PATH)
        logger.info(json.dumps({
            "event": "model_loaded",
            "model_path": MODEL_PATH
        }))
    except Exception as e:
        # If model fails to load, log and keep is_ready False
        logger.exception(json.dumps({
            "event": "model_load_failed",
            "error": str(e)
        }))
        app_state["is_ready"] = False
        return

    # Model loaded successfully
    app_state["is_ready"] = True

@app.get("/")
def home():
    return {"message": "IRIS Model API is running!"}

@app.get("/live_check", tags=["Probe"])
async def liveness_probe():
    if app_state["is_alive"]:
        return {"status": "alive"}
    return Response(status_code=500)

@app.get("/ready_check", tags=["Probe"])
async def readiness_probe():
    if app_state["is_ready"]:
        return {"status": "ready"}
    return Response(status_code=503)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Process-Time-ms"] = str(duration)
    return response

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    span = trace.get_current_span()
    # safe formatting for trace id; if no span/context, fallback to zeros
    try:
        trace_id = format(span.get_span_context().trace_id, "032x")
    except Exception:
        trace_id = "0" * 32

    logger.exception(json.dumps({
        "event": "unhandled_exception",
        "trace_id": trace_id,
        "path": str(request.url),
        "error": str(exc)
    }))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "trace_id": trace_id},
    )

@app.post("/predict")
async def predict(data: IrisData, request: Request):
    """
    Performs prediction using the loaded joblib model.
    Returns predicted label and optional confidence (if model supports predict_proba).
    """
    if not app_state["is_ready"] or not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="Model not ready")

    with tracer.start_as_current_span("model_inference") as span:
        start_time = time.time()
        # trace id safe-get
        try:
            trace_id = format(span.get_span_context().trace_id, "032x")
        except Exception:
            trace_id = "0" * 32

        try:
            features = np.array([[
                data.sepal_length,
                data.sepal_width,
                data.petal_length,
                data.petal_width
            ]])

            model = app.state.model
            # prediction
            pred = model.predict(features)
            # ensure it's a JSON-serializable element (int/str)
            predicted = pred[0].item() if hasattr(pred[0], "item") else pred[0]

            # try to get confidence if model supports predict_proba
            confidence: Optional[float] = None
            if hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(features)
                    # take max class probability for the single sample
                    confidence = float(np.max(proba))
                except Exception:
                    confidence = None

            latency = round((time.time() - start_time) * 1000, 2)

            logger.info(json.dumps({
                "event": "prediction",
                "trace_id": trace_id,
                "input": data.dict(),
                "predicted": predicted,
                "confidence": confidence,
                "latency_ms": latency,
                "status": "success"
            }))

            response = {"predicted_species": predicted}
            if confidence is not None:
                response["confidence"] = confidence
            return response

        except Exception as e:
            logger.exception(json.dumps({
                "event": "prediction_error",
                "trace_id": trace_id,
                "error": str(e)
            }))
            raise HTTPException(status_code=500, detail="Prediction failed")

