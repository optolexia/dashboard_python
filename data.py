from sqlalchemy import text
import pandas as pd
from db import pg_engine, mysql_engine
from cache import cache


@cache.memoize(timeout=3600)
def load_recordings():
    with pg_engine.connect() as conn:
        return pd.read_sql(
            text("""
            SELECT date_trunc('day', recording_date_time) AS recording_date,
                   CASE 
                       WHEN tracker_model ILIKE '%nexus%' THEN 'WebCam' 
                       ELSE 'EyeTracker' 
                   END AS tracker_group,
                   COUNT(DISTINCT screening_id) AS screenings_count
            FROM dbt_martynas_staging.stg_recording_headers
            WHERE recording_date_time >= DATE '2024-01-01'
            AND recording_date_time < CURRENT_DATE + INTERVAL '1 day'
            GROUP BY 1, 2
            ORDER BY 1
            """),
            conn
        )


@cache.memoize(timeout=3600)
def load_reading_time():
    with mysql_engine.connect() as conn:
        return pd.read_sql(
            text("""
            SELECT DATE(date) AS activity_date,
                   countryCode,
                   SUM(secondsSpent)/3600 AS hours_spent
            FROM readingapp.readingactivity
            WHERE date >= '2024-01-01'
            GROUP BY 1, 2
            ORDER BY 1
            """),
            conn
        )
