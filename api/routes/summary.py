from fastapi import APIRouter
from api.db import fetch_query_results

# Handles summary statistic queries.

router = APIRouter(prefix="/summary", tags=["Summary Statistics"])

@router.get("/statistics")
def get_summary_statistics():
    """Fetch precomputed summary statistics (latest + 1 week)."""
    query = "SELECT * FROM summary_statistics;"
    return fetch_query_results(query)