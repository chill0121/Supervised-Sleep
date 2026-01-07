import psycopg2
from database.db_utilities import *
from config.settings import *

# Materialized Views: For default dashboard data, refreshed during every database update.
mat_views_dict = {'sleep_calendar': # Probably add other important sleep data (HRV, Resting Heart Rate, Sleep Type Lengths, Total Length) and add to calendar in a minimalist way.
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
                            WHERE ds.day >= NOW() - INTERVAL '9 days'
                        ) t WHERE rn = 1;
                        """,
                  'weekly_averages':
                        """
                        CREATE MATERIALIZED VIEW weekly_averages AS
                        SELECT 
                            ROUND(AVG(sleep_score)::numeric, 0) as avg_sleep_score,
                            ROUND(AVG(activity_score)::numeric, 0) as avg_activity_score,
                            ROUND(AVG(readiness_score)::numeric, 0) as avg_readiness_score
                        FROM (
                            SELECT ds.score as sleep_score, da.score as activity_score, dr.score as readiness_score
                            FROM daily_sleep ds
                            JOIN daily_activity da ON ds.day = da.day
                            JOIN daily_readiness dr ON ds.day::DATE = dr.day
                            WHERE ds.day >= NOW() - INTERVAL '7 days'
                        ) t;
                        """,
                  'week_comparison':
                        """
                        CREATE MATERIALIZED VIEW week_comparison AS
                        WITH this_week AS (
                            SELECT 
                                AVG(ds.score) as sleep_score,
                                AVG(da.score) as activity_score,
                                AVG(dr.score) as readiness_score
                            FROM daily_sleep ds
                            JOIN daily_activity da ON ds.day = da.day
                            JOIN daily_readiness dr ON ds.day::DATE = dr.day
                            WHERE ds.day >= NOW() - INTERVAL '7 days'
                        ),
                        last_week AS (
                            SELECT 
                                AVG(ds.score) as sleep_score,
                                AVG(da.score) as activity_score,
                                AVG(dr.score) as readiness_score
                            FROM daily_sleep ds
                            JOIN daily_activity da ON ds.day = da.day
                            JOIN daily_readiness dr ON ds.day::DATE = dr.day
                            WHERE ds.day >= NOW() - INTERVAL '14 days'
                            AND ds.day < NOW() - INTERVAL '7 days'
                        )
                        SELECT 
                            ROUND((tw.sleep_score - lw.sleep_score)::numeric, 0) as sleep_delta,
                            ROUND((tw.activity_score - lw.activity_score)::numeric, 0) as activity_delta,
                            ROUND((tw.readiness_score - lw.readiness_score)::numeric, 0) as readiness_delta
                        FROM this_week tw, last_week lw;
                        """,
                  'sleep_breakdown':
                        """
                        CREATE MATERIALIZED VIEW sleep_breakdown AS
                        SELECT 
                            ROUND(AVG(deep_sleep_duration)::numeric, 0) as avg_deep_seconds,
                            ROUND(AVG(rem_sleep_duration)::numeric, 0) as avg_rem_seconds,
                            ROUND(AVG(light_sleep_duration)::numeric, 0) as avg_light_seconds,
                            ROUND(AVG(total_sleep_duration)::numeric, 0) as avg_total_seconds,
                            ROUND(AVG(total_sleep_duration / 3600.0)::numeric, 1) as avg_total_hours
                        FROM sleep_sessions
                        WHERE bedtime_start >= NOW() - INTERVAL '7 days'
                        AND type = 'long_sleep';
                        """,
                  'chronotype_stats':
                        """
                        CREATE MATERIALIZED VIEW chronotype_stats AS
                        WITH sleep_times AS (
                            SELECT 
                                CASE 
                                    WHEN EXTRACT(HOUR FROM (bedtime_start AT TIME ZONE 'America/Los_Angeles')::time) >= 18 
                                    THEN EXTRACT(EPOCH FROM (bedtime_start AT TIME ZONE 'America/Los_Angeles')::time) - 86400
                                    ELSE EXTRACT(EPOCH FROM (bedtime_start AT TIME ZONE 'America/Los_Angeles')::time)
                                END as bedtime_seconds,
                                EXTRACT(EPOCH FROM (bedtime_end AT TIME ZONE 'America/Los_Angeles')::time) as wake_seconds,
                                total_sleep_duration,
                                efficiency
                            FROM sleep_sessions
                            WHERE bedtime_start >= NOW() - INTERVAL '7 days'
                            AND type = 'long_sleep'
                        )
                        SELECT 
                            TO_CHAR((AVG(bedtime_seconds) + 86400 || ' seconds')::interval, 'HH12:MI AM') as avg_bedtime,
                            TO_CHAR((AVG(wake_seconds) || ' seconds')::interval, 'HH12:MI AM') as avg_wake_time,
                            ROUND(AVG(total_sleep_duration / 3600.0)::numeric, 1) as avg_duration_hours,
                            ROUND(AVG(efficiency)::numeric, 0) as avg_efficiency
                        FROM sleep_times;
                        """
                     }
# Virtual Views: To be used for dynamic queries during user selection.
# TODO: Add the rest once dashboard is further along.
views_dict = {'activity_details':
              """
              CREATE VIEW activity_details AS
              SELECT da.day, da.steps, da.active_calories, da.equivalent_walking_distance
              FROM daily_activity da;"""} 

def refresh_views(cursor, view_name):
    """Refreshes materialized views, to be used whenever new API data is inserted into database."""
    try:
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
        for view_name, query in mat_views_dict.items():
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