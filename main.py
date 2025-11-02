from fastapi import FastAPI
from pydantic import BaseModel
from joblib import load
import numpy as np

# Initialize FastAPI app
app = FastAPI()

# Load the trained model once at startup
model_path = "model-v1.joblib"  # Make sure this path is correct
model = load(model_path)
print(f"✅ Loaded model from {model_path}")

# Define the input data model
class IrisData(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.get("/")
def home():
    return {"message": "🌸 IRIS Model API is running!"}

@app.post("/predict")
def predict(data: IrisData):
    # Convert input to numpy array for model prediction
    features = np.array([[ 
        data.sepal_length, 
        data.sepal_width, 
        data.petal_length, 
        data.petal_width 
    ]])
    
    # Make prediction
    prediction = model.predict(features)
    species = prediction[0]
    
    return {"predicted_species": species}
