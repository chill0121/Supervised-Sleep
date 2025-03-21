from fastapi import APIRouter
from db import fetch_query_results

# Handles all sleep queries.

router = APIRouter(prefix="/sleep", tags=["Sleep Data"])

@router.get("/calendar")
def get_sleep_calendar():
    """Fetch precomputed sleep calendar for dashboard (last 6 months)."""
    query = "SELECT * FROM sleep_calendar;"
    return fetch_query_results(query)

@router.get("/sessions")
def get_sleep_sessions(start_date: str, end_date: str):
    """Fetch user-selected sleep sessions."""
    query = """
    SELECT * FROM sleep_sessions 
    WHERE bedtime_start >= %s AND bedtime_end <= %s
    """
    return fetch_query_results(query, (start_date, end_date))