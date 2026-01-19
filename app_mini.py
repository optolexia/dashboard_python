from flask import Flask, redirect, url_for, session, request
from flask_session import Session
import msal
import os
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

# ------------------------
# Flask session config
# ------------------------
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ------------------------
# Azure AD config
# ------------------------
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
TENANT_ID = os.environ["TENANT_ID"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"
SCOPE = ["User.Read"]

# ------------------------
# MSAL helper
# ------------------------
def _build_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

# ------------------------
# Routes
# ------------------------

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    return f"""
        <h1>Logged in</h1>
        <p>Name: {user.get("name")}</p>
        <p>Email: {user.get("preferred_username")}</p>
        <a href="/logout">Logout</a>
    """

@app.route("/login")
def login():
    msal_app = _build_msal_app()

    flow = msal_app.initiate_auth_code_flow(
        scopes=SCOPE,
        redirect_uri=url_for("authorized", _external=True),
    )

    session["auth_flow"] = flow
    return redirect(flow["auth_uri"])

@app.route(REDIRECT_PATH)
def authorized():
    if "auth_flow" not in session:
        return "Auth flow missing", 400

    msal_app = _build_msal_app()

    result = msal_app.acquire_token_by_auth_code_flow(
        session["auth_flow"],
        request.args,
    )

    if "id_token_claims" not in result:
        return f"Login failed: {result}", 401

    user = result["id_token_claims"]

    # Org-only enforcement
    if user.get("tid") != TENANT_ID:
        return "Access denied (wrong tenant)", 403

    session["user"] = user
    session.pop("auth_flow", None)

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
    )

# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    app.run(host="localhost", port=8050, debug=True)
