from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from sklearn.linear_model import LinearRegression

router = APIRouter()

class ForecastRequest(BaseModel):
    medicine_id: int
    past_months_sales: List[float] = Field(..., min_length=2, description="Sales data for at least the past 2 months")

@router.post("/forecast", status_code=status.HTTP_200_OK)
def forecast_demand(request: ForecastRequest):
    """
    Use LinearRegression to train a model on the past months' sales data.
    Predict the expected demand for the next month and recommend a stock level.
    """
    sales_data = request.past_months_sales
    
    if len(sales_data) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 months of sales data are required to perform forecasting."
        )
        
    # X represents the month index [1, 2, 3, ...]
    X = np.array(range(1, len(sales_data) + 1)).reshape(-1, 1)
    # y represents the actual sales figures
    y = np.array(sales_data)
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict for the next consecutive month
    next_month_index = np.array([[len(sales_data) + 1]])
    prediction = model.predict(next_month_index)[0]
    
    # Ensure prediction is non-negative and rounded to nearest integer
    predicted_demand = max(0, int(round(prediction)))
    
    # Calculate recommended stock level (+20% safety buffer)
    recommended_stock_level = int(round(predicted_demand * 1.2))
    
    return {
        "medicine_id": request.medicine_id,
        "predicted_demand": predicted_demand,
        "recommended_stock_level": recommended_stock_level
    }
