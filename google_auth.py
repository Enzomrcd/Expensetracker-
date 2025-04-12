
import json
import os
import datetime
import logging

import requests
from flask import Blueprint, redirect, request, url_for, session, flash
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient
from app import db

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Get the redirect URL based on environment
REPLIT_DOMAIN = os.environ.get("REPLIT_DOMAIN") or os.environ.get("REPLIT_DEV_DOMAIN", "localhost")
REDIRECT_URL = "https://" + REPLIT_DOMAIN + "/google_login/callback" if REPLIT_DOMAIN else "http://localhost:5000/google_login/callback"

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

# Create the Blueprint
google_auth = Blueprint("google_oauth", __name__, url_prefix="/google_login")

@google_auth.route("/login")
def login():
    try:
        logging.info(f"OAuth redirect URL: {REDIRECT_URL}")
        # Check if Google OAuth is configured
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            # Not configured, redirect to demo login
            return redirect(url_for("demo_login"))
        
        # Find out what URL to hit for Google login
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=REDIRECT_URL,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash("Login failed. Please try again.", "error")
        return redirect(url_for("index"))

@google_auth.route("/callback")
def callback():
    try:
        # Check if Google OAuth is configured
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            flash("Google OAuth is not configured properly", "error")
            return redirect(url_for("index"))
        
        # Get authorization code Google sent back
        code = request.args.get("code")
        if not code:
            flash("Authentication failed - no code received", "error")
            return redirect(url_for("index"))

        # Find out what URL to hit to get tokens
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare and send request to get tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=REDIRECT_URL,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        if userinfo_response.json().get("email_verified"):
            # Get user data
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            users_name = userinfo_response.json().get("given_name", users_email.split("@")[0])
            
            # Create user in db
            user = User(
                uid=unique_id,
                email=users_email,
                display_name=users_name
            )
            
            # Log user in
            login_user(user)
            session['user_id'] = unique_id
            
            return redirect(url_for("dashboard"))
        else:
            flash("User email not verified by Google.", "error")
            return redirect(url_for("index"))
            
    except Exception as e:
        logging.error(f"Callback error: {str(e)}")
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("index"))

@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))
