from fastapi import FastAPI
from api.routes import sleep, heartrate, activity, summary, advice, refresh

# Handles API routing.

app = FastAPI(title="Supervised Sleep API", version="1.0")

# Include API routes
app.include_router(sleep.router)
app.include_router(heartrate.router)
app.include_router(activity.router)
app.include_router(summary.router)
app.include_router(advice.router)
app.include_router(refresh.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Supervised Sleep API"} 