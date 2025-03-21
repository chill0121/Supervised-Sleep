import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

# Handles PostgreSQL queries.

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        # password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        cursor_factory=RealDictCursor
    )

# Function to execute queries
def fetch_query_results(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results