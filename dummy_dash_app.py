from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
#from dash.testing.plugin import dash_br


def create_dash_app(flask_server):
    dash_app = Dash(
        __name__,
        server=flask_server,
        url_base_pathname="/app/",
    )

    # --- Dummy data (replace with yours) ---
    df = pd.DataFrame({
        "x": [1, 2, 3, 4],
        "y": [10, 20, 15, 30],
    })

    dash_app.layout = html.Div(
        style={"padding": "24px"},
        children=[
            html.H1("Lexplore User Activities (Dev)"),
            dcc.Graph(id="example-graph"),
            html.A("Logout", href="/logout"),
        ],
    )

    @dash_app.callback(
        Output("example-graph", "figure"),
        Input("example-graph", "id"),
    )
    def update_graph(_):
        return px.line(df, x="x", y="y", title="Example Dashboard")

    return dash_app

def create_dash_app_mini(flask_server):
    dash_app = Dash(
        __name__,
        server=flask_server,
        url_base_pathname="/app/",
    )

    dash_app.layout = html.Div(
        style={"padding": "40px"},
        children=[
            html.H1("Protected Dash App"),
            #html.P("If you see this, login works."),
            dcc.Graph(id="example-graph"),
            html.A("Logout", href="/logout"),
        ],
    )