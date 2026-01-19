from flask import Flask, redirect, session, request, url_for
from flask_session import Session
import msal
import os
import dotenv
dotenv.load_dotenv()
from dash import Dash, html

# =========================
# Flask setup
# =========================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# =========================
# Azure AD config
# =========================
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
TENANT_ID = os.environ["TENANT_ID"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"
SCOPE = ["User.Read"]

def build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache,
    )

# =========================
# Routes
# =========================
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    return redirect("/app/")

@app.route("/login")
def login():
    msal_app = build_msal_app()
    flow = msal_app.initiate_auth_code_flow(
        SCOPE,
        redirect_uri=url_for("authorized", _external=True),
    )
    session["flow"] = flow
    return redirect(flow["auth_uri"])

@app.route(REDIRECT_PATH)
def authorized():
    if "flow" not in session:
        return redirect("/")

    msal_app = build_msal_app()
    result = msal_app.acquire_token_by_auth_code_flow(
        session["flow"],
        request.args,
    )

    if "id_token_claims" not in result:
        return "Login failed", 401

    if result["id_token_claims"]["tid"] != TENANT_ID:
        return "Forbidden", 403

    session["user"] = result["id_token_claims"]
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
    )



# =========================
# HARD protection
# =========================

@app.before_request
def block_unauthenticated():
    path = request.path

    protected_paths = (
            path.startswith("/app")
            or path.startswith("/_dash")
            #or path.startswith("/_dash-component-suites")
    )
    print("session: ", session)
    print("path: ", path)
    print("protected? ", protected_paths)

    if protected_paths and "user" not in session:
        print(path, " ---> redirecting to login")
        return redirect("/login")

# =========================
# Dash app
# =========================
from dummy_dash_app import create_dash_app

dash_app=create_dash_app(app)

# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(host="localhost", port=8050, debug=True)
