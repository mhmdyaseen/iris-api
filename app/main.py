from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class IrisData(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.get("/")
def home():
    return {"message": "IRIS API is running!"}

@app.post("/predict")
def predict(data: IrisData):
    # Dummy logic (replace later with ML model)
    if data.petal_length < 2:
        species = "setosa"
    elif data.petal_length < 5:
        species = "versicolor"
    else:
        species = "virginica"
    return {"species": species}
