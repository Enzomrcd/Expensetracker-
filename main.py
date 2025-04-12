from app import app, has_google_oauth

# We'll let app.py handle the Google Auth blueprint registration

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
