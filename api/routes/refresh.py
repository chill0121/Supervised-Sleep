from fastapi import APIRouter
from db import get_db_connection

# Manually refreshes materialized views.

router = APIRouter(prefix="/refresh", tags=["Database Management"])

@router.post("/")
def refresh_materialized_views():
    """Refresh all materialized views after inserting new data."""
    queries = [
        "REFRESH MATERIALIZED VIEW sleep_calendar;",
        "REFRESH MATERIALIZED VIEW heartrate_trends;",
        "REFRESH MATERIALIZED VIEW stress_trends;",
        "REFRESH MATERIALIZED VIEW summary_statistics;"
    ]
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for query in queries:
        cursor.execute(query)

    connection.commit()
    cursor.close()
    connection.close()
    
    return {"message": "Materialized views refreshed successfully"}
