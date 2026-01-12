from fastapi import APIRouter
from api.db import fetch_query_results

# Handles summary statistic queries.

router = APIRouter(prefix="/summary", tags=["Summary Statistics"])

@router.get("/statistics")
def get_summary_statistics():
    """Fetch precomputed summary statistics (latest + 1 week)."""
    query = "SELECT * FROM summary_statistics;"
    return fetch_query_results(query)

@router.get("/weekly_averages")
def get_weekly_averages():
    """Fetch 7-day average scores."""
    query = "SELECT * FROM weekly_averages;"
    return fetch_query_results(query)

@router.get("/week_comparison")
def get_week_comparison():
    """Fetch this week vs last week comparison."""
    query = "SELECT * FROM week_comparison;"
    return fetch_query_results(query)

@router.get("/sleep_breakdown")
def get_sleep_breakdown():
    """Fetch sleep stage breakdown (7-day average)."""
    query = "SELECT * FROM sleep_breakdown;"
    return fetch_query_results(query)

@router.get("/chronotype")
def get_chronotype_stats():
    """Fetch chronotype/sleep timing statistics."""
    query = "SELECT * FROM chronotype_stats;"
    return fetch_query_results(query)

@router.get("/correlations")
def get_sleep_correlations():
    """Fetch top correlations with sleep quality."""
    query = "SELECT * FROM sleep_correlations;"
    return fetch_query_results(query)