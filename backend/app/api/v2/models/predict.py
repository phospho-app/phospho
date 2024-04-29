from pydantic import BaseModel
from typing import Optional


class PredictRequest(BaseModel):
    inputs: (
        list  # List of inputs to make predictions on, for now a list of text strings
    )
    model: str  # Model identifier


class PredictResponse(BaseModel):
    predictions: list  # List of predictions (booleans for now
