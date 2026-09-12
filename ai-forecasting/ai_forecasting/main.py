from fastapi import FastAPI
from .api.routes import router

app = FastAPI(title="AI Demand Forecasting API")

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Hello World from AI Demand Forecasting Service"}

