import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

db = SQLAlchemy(app)


@app.get("/health")
def index():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
