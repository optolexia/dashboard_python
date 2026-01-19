# dash_app.py
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from cache import cache
from data import load_recordings, load_reading_time  # cached functions
import os

def create_dash_app(flask_server):
    """
    Create a Dash app bound to the given Flask server.
    Layout and callbacks are defined here.
    """
    # ─────────────────────────────────────────────
    # Initialize cache with Flask server
    # ─────────────────────────────────────────────
    cache.init_app(flask_server, config={"CACHE_TYPE": "SimpleCache"})

    # Load data AFTER cache is initialized
    recordings_df = load_recordings()
    reading_df = load_reading_time()

    # ─────────────────────────────────────────────
    # Create Dash app
    # ─────────────────────────────────────────────
    dash_app = Dash(
        __name__,
        server=flask_server,
        url_base_pathname="/app/",
        suppress_callback_exceptions=True,
    )

    # ─────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────
    dash_app.layout = html.Div(
        style={"padding": "24px", "fontFamily": "Arial"},
        children=[
            html.H1("Lexplore User Activities (Dev)"),
            html.Div(
                style={"display": "flex", "gap": "24px", "marginBottom": "24px"},
                children=[
                    dcc.DatePickerRange(
                        id="date-range",
                        start_date=recordings_df["recording_date"].min(),
                        end_date=recordings_df["recording_date"].max(),
                        display_format="YYYY-MM-DD"
                    ),
                    dcc.Dropdown(
                        id="tracker-filter",
                        options=[
                            {"label": "WebCam", "value": "WebCam"},
                            {"label": "EyeTracker", "value": "EyeTracker"},
                        ],
                        value=["WebCam", "EyeTracker"],
                        multi=True,
                    ),
                    dcc.Dropdown(
                        id="country-filter",
                        options=[{"label": c, "value": c} for c in sorted(reading_df["countryCode"].dropna().unique())],
                        value=sorted(reading_df["countryCode"].dropna().unique()),
                        multi=True,
                    ),
                ]
            ),
            dcc.Graph(id="recordings-graph"),
            dcc.Graph(id="reading-graph"),
            html.A("Logout", href="/logout"),
        ]
    )

    # ─────────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────────
    @dash_app.callback(
        Output("recordings-graph", "figure"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("tracker-filter", "value"),
    )
    def update_recordings(start_date, end_date, trackers):
        df = recordings_df.copy()
        if start_date:
            df = df[df["recording_date"] >= start_date]
        if end_date:
            df = df[df["recording_date"] <= end_date]
        if trackers:
            df = df[df["tracker_group"].isin(trackers)]

        fig = px.line(
            df,
            x="recording_date",
            y="screenings_count",
            color="tracker_group",
            title="Screenings per Day",
            labels={
                "recording_date": "Date",
                "screenings_count": "Number of Screenings",
                "tracker_group": "Tracker Type"
            }
        )
        return fig

    @dash_app.callback(
        Output("reading-graph", "figure"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("country-filter", "value"),
    )
    def update_reading(start_date, end_date, countries):
        df = reading_df.copy()
        if start_date:
            start = pd.to_datetime(start_date).tz_convert(None) if hasattr(pd.to_datetime(start_date), 'tz') else pd.to_datetime(start_date)
            df = df[df["activity_date"] >= start]
        if end_date:
            end = pd.to_datetime(end_date).tz_convert(None) if hasattr(pd.to_datetime(end_date), 'tz') else pd.to_datetime(end_date)
            df = df[df["activity_date"] <= end]
        if countries:
            df = df[df["countryCode"].isin(countries)]
        if df.empty:
            return px.line(title="No data for selected filters")

        fig = px.line(
            df,
            x="activity_date",
            y="hours_spent",
            color="countryCode",
            title="Reading Time per Day",
            labels={
                "activity_date": "Date",
                "hours_spent": "Hours Spent Reading",
                "countryCode": "Country"
            }
        )
        return fig

    return dash_app
