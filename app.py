from dash import Dash, dcc, html
import plotly.express as px
from cache import cache
import dotenv
dotenv.load_dotenv()

# ─────────────────────────────────────────────
# Dash app & Flask server
# ─────────────────────────────────────────────

app = Dash(__name__)
server = app.server

# Attach cache to Flask server
cache.init_app(server)

# ─────────────────────────────────────────────
# Import data AFTER cache is initialized
# ─────────────────────────────────────────────

from data import load_recordings, load_reading_time  # noqa: E402

# ─────────────────────────────────────────────
# Load cached data
# ─────────────────────────────────────────────

recordings_df = load_recordings()
reading_df = load_reading_time()

# ─────────────────────────────────────────────
# Create figures
# ─────────────────────────────────────────────

fig_recordings = px.line(
    recordings_df,
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

fig_reading = px.line(
    reading_df,
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

# ─────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────

app.layout = html.Div(
    style={"padding": "24px", "fontFamily": "Arial"},
    children=[
        html.H1("Lexplore User Activity (Dev)"),
        dcc.Graph(figure=fig_recordings),
        dcc.Graph(figure=fig_reading),
    ]
)

# ─────────────────────────────────────────────
# Run locally
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
