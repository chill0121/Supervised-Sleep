from fastapi import APIRouter
from api.db import fetch_query_results

# Handles ML-generated daily advice.

router = APIRouter(prefix="/advice", tags=["Actionable Advice"])

@router.get("/")
def get_actionable_advice():
    """Fetch actionable sleep improvement advice (placeholder for ML model)."""
    query = "SELECT * FROM actionable_advice;"
    return fetch_query_results(query)