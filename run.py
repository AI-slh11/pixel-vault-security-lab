from app import create_app

app = create_app()


if __name__ == "__main__":
    # The app is intentionally local-only. Do not change this to 0.0.0.0.
    app.run(host="127.0.0.1", port=5000, debug=False)
