from fastapi import APIRouter
from db import fetch_query_results

# Handles all activity queries.

router = APIRouter(prefix="/activity", tags=["Activity Data"])

@router.get("/summary")
def get_activity_summary():
    """Fetch daily activity summaries."""
    query = "SELECT * FROM activity_details;"
    return fetch_query_results(query)

@router.get("/custom")
def get_custom_activity(start_date: str, end_date: str):
    """Fetch activity data for a custom date range."""
    query = """
    SELECT * FROM daily_activity
    WHERE day BETWEEN %s AND %s
    """
    return fetch_query_results(query, (start_date, end_date))