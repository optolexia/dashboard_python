from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from cache import cache
import os
from functools import wraps
from flask import Flask, session, redirect, url_for, request
from flask_session import Session
import msal
import dotenv
dotenv.load_dotenv()

# ─────────────────────────────────────────────
# Dash app & Flask server
# ─────────────────────────────────────────────

server = Flask(__name__)

# Attach cache
cache.init_app(server)

# ─────────────────────────────────────────────
# Azure AD Authentication config
# ─────────────────────────────────────────────

FLASK_SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
server.config["SECRET_KEY"] = FLASK_SECRET_KEY
server.config["SESSION_TYPE"] = "filesystem"
Session(server)

CLIENT_ID = os.environ["CLIENT_ID"]
TENANT_ID = os.environ["TENANT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"
SCOPE = ["User.Read"]  # minimal permissions


app = Dash(
    __name__,
    server=server,
    url_base_pathname="/app/"   # Dash will now live at /app/
)
# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@server.route("/login")
def login():
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=url_for("authorized", _external=True)
    )
    return redirect(auth_url)

@server.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return redirect("/app/")  # send logged-in users to Dash


@server.route(REDIRECT_PATH)
def authorized():
    code = request.args.get("code")
    if not code:
        return "Authorization failed", 401

    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=url_for("authorized", _external=True)
    )

    if "id_token_claims" in result:
        user = result["id_token_claims"]
        # Enforce your tenant only
        if user.get("tid") != TENANT_ID:
            return "Access denied: not in your organization", 403
        session["user"] = user
    else:
        return "Authentication failed", 401

    return redirect("/")

@server.before_request
def protect_dash():
    # Any request under /app/ requires login
    if request.path.startswith("/app/") and "user" not in session:
        return redirect("/login")



@server.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
    )

# ─────────────────────────────────────────────
# Import data AFTER cache
# ─────────────────────────────────────────────
from data import load_recordings, load_reading_time  # noqa: E402

recordings_df = load_recordings()
reading_df = load_reading_time()

# ─────────────────────────────────────────────
# Layout & graphs
# ─────────────────────────────────────────────

# layout no longer touches session
def serve_layout():
    return html.Div(
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
        ]
    )

app.layout = serve_layout

# ─────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────

@app.callback(
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

@app.callback(
    Output("reading-graph", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("country-filter", "value"),
)
def update_reading(start_date, end_date, countries):
    df = reading_df.copy()

    # filter dates
    if start_date:
        start = pd.to_datetime(start_date).tz_convert(None) if hasattr(pd.to_datetime(start_date),
                                                                       'tz') else pd.to_datetime(start_date)
        df = df[df["activity_date"] >= start]

    if end_date:
        end = pd.to_datetime(end_date).tz_convert(None) if hasattr(pd.to_datetime(end_date), 'tz') else pd.to_datetime(
            end_date)
        df = df[df["activity_date"] <= end]

    # filter countries
    if countries:
        df = df[df["countryCode"].isin(countries)]

    # handle empty df
    if df.empty:
        print("No recordings found")
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

# ─────────────────────────────────────────────
# Run app
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8050)
