import os

import psycopg
import redis
from flask import Flask, Response, request


app = Flask(__name__)
cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "cache"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
)


def database_connection():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def create_table():
    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                text text NOT NULL
            )
            """
        )


@app.get("/")
def index():
    visits = cache.incr("visits")
    return Response(f"Docker Compose demo - visits: {visits}\n", mimetype="text/plain")


@app.get("/notes")
def notes():
    with database_connection() as connection:
        rows = connection.execute("SELECT id, text FROM notes ORDER BY id").fetchall()
    body = "\n".join(f"{note_id}: {text}" for note_id, text in rows)
    return Response((body or "(no notes)") + "\n", mimetype="text/plain")


@app.get("/notes/add")
def add_note():
    text = request.args.get("text", "").strip()
    if not text:
        return Response("text is required\n", status=400, mimetype="text/plain")
    with database_connection() as connection:
        connection.execute("INSERT INTO notes (text) VALUES (%s)", (text,))
    return Response(f"added: {text}\n", status=201, mimetype="text/plain")


create_table()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
