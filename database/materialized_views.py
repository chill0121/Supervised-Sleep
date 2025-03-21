import psycopg2
from database.db_utilities import * #create_table, delete_table, table_list, DB_NAME, DB_USER, DB_HOST, DB_PORT
from config.settings import * #BASE_DIR, TOKEN_PATH, DATA_DIR, TODAY, TODAY_DATETIME

views_dict = {'sleep_calendar':
                    """
                    CREATE MATERIALIZED VIEW sleep_calendar AS
                    SELECT day, score AS sleep_score
                    FROM daily_sleep
                    WHERE day >= NOW() - INTERVAL '6 months'
                    ORDER BY day DESC;
                    """,
              'heartrate_trends': # TODO: rolling statistics here.
                    """
                    CREATE MATERIALIZED VIEW heartrate_trends AS
                    SELECT timestamp::DATE AS day, 
                        AVG(bpm) AS avg_heart_rate,
                        MIN(bpm) AS min_heart_rate,
                        MAX(bpm) AS max_heart_rate
                    FROM heartrate
                    WHERE timestamp >= NOW() - INTERVAL '3 months'
                    GROUP BY day
                    ORDER BY day DESC;
                    """,
            #   'stress_trends':
            #         """
            #         CREATE MATERIALIZED VIEW stress_trends AS
            #         SELECT day, score AS stress_score
            #         FROM daily_stress
            #         WHERE day >= NOW() - INTERVAL '3 months'
            #         ORDER BY day DESC;
            #         """,
              'summary_statistics':
                    """
                    CREATE MATERIALIZED VIEW summary_statistics AS
                    SELECT day, 
                        sleep_score, 
                        activity_score, 
                        readiness_score
                    FROM (
                        SELECT ds.day, ds.score AS sleep_score, 
                            da.score AS activity_score, 
                            dr.score AS readiness_score,
                            ROW_NUMBER() OVER (PARTITION BY ds.day ORDER BY ds.day DESC) AS rn
                        FROM daily_sleep ds
                        JOIN daily_activity da ON ds.day = da.day
                        JOIN daily_readiness dr ON ds.day = dr.day
                        WHERE ds.day >= NOW() - INTERVAL '7 days'
                    ) t WHERE rn = 1;
                    """
            }

def refresh_views(cursor, view_name):
    """Refreshes materialized views, to be used whenever new API data is inserted into database."""
    try:
        # for view_name in views_dict.keys():
        #     cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name};")
        #     logging.info(f"Refreshed materialized view: {view_name}")
        cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name};")
        logging.info(f"Refreshed materialized view: {view_name}")
    except psycopg2.Error as e:
        logging.error(f"Error refreshing materialized views': {e}")

def view_exists(cursor, view_name):
    """Checks if a materialized view exists in the database."""
    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews WHERE matviewname = %s
                ) AS "exists";""", 
                (view_name,))
        return cursor.fetchone()[0]
    except:
        logging.error(f"Error checking if materialized view exists:")
        return False

def initialize_materialized_views(connection):
    """Creates materialized views if they don't exist, otherwise refreshes them."""
    try:
        cursor = connection.cursor()
        for view_name, query in views_dict.items():
            if view_exists(cursor, view_name):
                logging.info(f"View {view_name} already exists. Refreshing instead.")
                refresh_views(cursor, view_name)
            else:
                cursor.execute(query)
                logging.info(f"Created materialized view: {view_name}")

        # Commit changes
        connection.commit()
        logging.info("Materialized views initialized successfully.")

    except psycopg2.Error as e:
        connection.rollback()
        logging.error(f"Error initializing materialized views: {e}")
    finally:
        cursor.close()