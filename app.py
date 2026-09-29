import hmac
import json
import os
import secrets
import sqlite3
import tempfile
import urllib.error
import urllib.request
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("DBR_DATABASE", BASE_DIR / "dbr.sqlite3"))
NEWS_DATA_PATH = BASE_DIR / "data" / "news.json"
RANKS = [
    "Курсант",
    "Капрал",
    "Сержант",
    "Старший Сержант",
    "Молодший Лейтенант",
    "Лейтенант",
    "Старший Лейтенант",
    "Капітан",
    "Майор",
    "Підполковник",
    "Полковник",
    "Заступник Директора ДБР",
    "Директор ДБР",
]
DEPARTMENTS = [
    "ТСВ",
    "ОСД",
]
ROBLOX_USERNAME_URL = "https://users.roblox.com/v1/usernames/users"
ROBLOX_AVATAR_HEADSHOT_URL = "https://thumbnails.roblox.com/v1/users/avatar-headshot"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
ADMIN_TOKEN = os.environ.get("DBR_ADMIN_TOKEN") or secrets.token_urlsafe(24)


def connect_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_db()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roblox_user_id INTEGER NOT NULL UNIQUE,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                rank TEXT NOT NULL,
                department TEXT NOT NULL,
                call_sign TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )


def require_admin():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or not hmac.compare_digest(token, ADMIN_TOKEN):
        return jsonify({"error": "Потрібен дійсний ключ адміністратора."}), 401
    return None


def staff_record(row):
    user_id = row["roblox_user_id"]
    return {
        "id": row["id"],
        "roblox_user_id": user_id,
        "username": row["username"],
        "display_name": row["display_name"],
        "rank": row["rank"],
        "department": row["department"],
        "call_sign": row["call_sign"],
        "avatar_url": f"/api/avatar/{user_id}/headshot",
        "profile_url": f"https://www.roblox.com/users/{user_id}/profile",
    }


def fetch_json(url, *, payload=None, method="GET"):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "User-Agent": "DBR-RP-Roster/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Не вдалося зв'язатися з Roblox. Перевір username та спробуй ще раз.") from exc


def resolve_roblox_user(username):
    response = fetch_json(
        ROBLOX_USERNAME_URL,
        payload={"usernames": [username], "excludeBannedUsers": True},
        method="POST",
    )
    users = response.get("data", [])
    if not users:
        raise ValueError("Гравця з таким Roblox username не знайдено.")
    return users[0]


def validate_staff_payload(payload):
    username = str(payload.get("username", "")).strip().lstrip("@")
    rank = str(payload.get("rank", "")).strip()
    department = str(payload.get("department", "")).strip()
    call_sign = str(payload.get("call_sign", "")).strip()
    if len(username) < 3 or len(username) > 20 or not username.replace("_", "").isalnum():
        raise ValueError("Вкажи правильний Roblox username (до 20 символів).")
    if rank not in RANKS:
        raise ValueError("Обери звання зі списку.")
    if department not in DEPARTMENTS:
        raise ValueError("Обери відділ зі списку.")
    if len(call_sign) > 40:
        raise ValueError("Позивний має бути коротшим за 40 символів.")
    return username, rank, department, call_sign


def read_news_records():
    if not NEWS_DATA_PATH.exists():
        return []
    with NEWS_DATA_PATH.open("r", encoding="utf-8") as source:
        records = json.load(source)
    if not isinstance(records, list):
        raise ValueError("Файл новин має містити список публікацій.")
    return records


def write_news_records(records):
    NEWS_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", dir=NEWS_DATA_PATH.parent, delete=False
        ) as target:
            temporary_path = Path(target.name)
            json.dump(records, target, ensure_ascii=False, indent=2)
            target.write("\n")
        os.replace(temporary_path, NEWS_DATA_PATH)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def validate_news_payload(payload):
    title = str(payload.get("title", "")).strip()
    category = str(payload.get("category", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    raw_content = str(payload.get("content", "")).strip()
    raw_date = str(payload.get("date", "")).strip()
    if not title or len(title) > 140:
        raise ValueError("Заголовок обов'язковий і має бути до 140 символів.")
    if not category or len(category) > 40:
        raise ValueError("Вкажи розділ новини (до 40 символів).")
    if len(summary) > 300:
        raise ValueError("Короткий опис має бути до 300 символів.")
    if not raw_content or len(raw_content) > 8000:
        raise ValueError("Текст новини обов'язковий і має бути до 8000 символів.")
    if len(raw_date) != 10:
        raise ValueError("Вкажи дату новини.")
    try:
        date.fromisoformat(raw_date)
    except ValueError as exc:
        raise ValueError("Дата новини має бути у форматі РРРР-ММ-ДД.") from exc
    content = [paragraph.strip() for paragraph in raw_content.splitlines() if paragraph.strip()]
    return {
        "id": uuid4().hex,
        "date": raw_date,
        "category": category,
        "title": title,
        "summary": summary,
        "content": content,
    }


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/news.html")
def news_page():
    return send_from_directory(BASE_DIR, "news.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(BASE_DIR, "styles.css")


@app.get("/dbr-mark.svg")
def logo_mark():
    return send_from_directory(BASE_DIR, "dbr-mark.svg", mimetype="image/svg+xml")


@app.get("/photo_2026-09-29_14-04-02.jpg")
def building_image():
    return send_from_directory(BASE_DIR, "photo_2026-09-29_14-04-02.jpg", mimetype="image/jpeg")


@app.get("/staff.js")
def staff_script():
    return send_from_directory(BASE_DIR, "staff.js", mimetype="text/javascript")


@app.get("/admin.js")
def admin_script():
    return send_from_directory(BASE_DIR, "admin.js", mimetype="text/javascript")


@app.get("/news.js")
def news_script():
    return send_from_directory(BASE_DIR, "news.js", mimetype="text/javascript")


@app.get("/news-ticker.js")
def news_ticker_script():
    return send_from_directory(BASE_DIR, "news-ticker.js", mimetype="text/javascript")


@app.get("/data/<path:filename>")
def public_data(filename):
    if filename not in {"news.json", "staff.json"}:
        return jsonify({"error": "Файл не знайдено."}), 404
    return send_from_directory(BASE_DIR / "data", filename)


@app.get("/pages-config.json")
def pages_configuration():
    return jsonify({"static": False})


@app.get("/admin")
def admin_page():
    return send_from_directory(BASE_DIR, "admin.html")


@app.get("/api/staff")
def list_staff():
    with closing(connect_db()) as connection, connection:
        rows = connection.execute(
            "SELECT * FROM staff ORDER BY CASE rank "
            + " ".join(f"WHEN '{rank}' THEN {index}" for index, rank in enumerate(RANKS))
            + " ELSE 99 END, username COLLATE NOCASE"
        ).fetchall()
    return jsonify([staff_record(row) for row in rows])


@app.get("/api/admin/check")
def check_admin():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    return jsonify({"ok": True})


@app.post("/api/staff")
def add_staff():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    try:
        username, rank, department, call_sign = validate_staff_payload(payload)
        roblox_user = resolve_roblox_user(username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502

    try:
        with closing(connect_db()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO staff (roblox_user_id, username, display_name, rank, department, call_sign, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    roblox_user["id"],
                    roblox_user["name"],
                    roblox_user.get("displayName") or roblox_user["name"],
                    rank,
                    department,
                    call_sign,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            row = connection.execute("SELECT * FROM staff WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Цей Roblox-гравець вже є в особовому складі."}), 409
    return jsonify(staff_record(row)), 201


@app.put("/api/staff/<int:staff_id>")
def update_staff(staff_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    try:
        username, rank, department, call_sign = validate_staff_payload(payload)
        roblox_user = resolve_roblox_user(username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502

    try:
        with closing(connect_db()) as connection, connection:
            cursor = connection.execute(
                "UPDATE staff SET roblox_user_id = ?, username = ?, display_name = ?, rank = ?, department = ?, call_sign = ? WHERE id = ?",
                (
                    roblox_user["id"],
                    roblox_user["name"],
                    roblox_user.get("displayName") or roblox_user["name"],
                    rank,
                    department,
                    call_sign,
                    staff_id,
                ),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "Працівника не знайдено."}), 404
            row = connection.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Цей Roblox-гравець вже є в особовому складі."}), 409
    return jsonify(staff_record(row))


@app.delete("/api/staff/<int:staff_id>")
def delete_staff(staff_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    with closing(connect_db()) as connection, connection:
        cursor = connection.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "Працівника не знайдено."}), 404
    return jsonify({"ok": True})


@app.get("/api/avatar/<int:user_id>/headshot")
def avatar_headshot(user_id):
    if user_id < 1:
        return jsonify({"error": "Некоректний Roblox user ID."}), 400
    try:
        response = fetch_json(
            f"{ROBLOX_AVATAR_HEADSHOT_URL}?userIds={user_id}&size=180x180&format=Png&isCircular=false"
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502
    thumbnails = response.get("data", [])
    image_url = thumbnails[0].get("imageUrl") if thumbnails else None
    if not image_url or thumbnails[0].get("state") != "Completed":
        return jsonify({"error": "Roblox не повернув аватар для цього гравця."}), 502
    image_host = image_url.split("/", 3)[2].lower() if image_url.startswith("https://") else ""
    if image_host != "rbxcdn.com" and not image_host.endswith(".rbxcdn.com"):
        return jsonify({"error": "Roblox повернув некоректне посилання на аватар."}), 502
    return redirect(image_url, code=302)


@app.get("/api/config")
def public_config():
    return jsonify({"ranks": RANKS, "departments": DEPARTMENTS})


@app.get("/api/admin/news")
def admin_news_list():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    try:
        records = read_news_records()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return jsonify({"error": f"Не вдалося прочитати новини: {exc}"}), 500
    return jsonify(sorted(records, key=lambda item: item.get("date", ""), reverse=True))


@app.post("/api/news")
def add_news():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    try:
        record = validate_news_payload(payload)
        records = read_news_records()
        records.append(record)
        write_news_records(records)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except (OSError, json.JSONDecodeError) as exc:
        return jsonify({"error": f"Не вдалося зберегти новину: {exc}"}), 500
    return jsonify(record), 201


@app.delete("/api/news/<string:news_id>")
def delete_news(news_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    try:
        records = read_news_records()
        remaining = [record for record in records if record.get("id") != news_id]
        if len(remaining) == len(records):
            return jsonify({"error": "Новину не знайдено."}), 404
        write_news_records(remaining)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return jsonify({"error": f"Не вдалося видалити новину: {exc}"}), 500
    return jsonify({"ok": True})


if __name__ == "__main__":
    initialize_db()
    print("DBR roster is running at http://127.0.0.1:5000")
    if not os.environ.get("DBR_ADMIN_TOKEN"):
        print(f"Temporary admin token (copy this into /admin): {ADMIN_TOKEN}")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
