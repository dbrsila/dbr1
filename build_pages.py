import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "_site"
PUBLIC_FILES = (
    "index.html",
    "news.html",
    "styles.css",
    "staff.js",
    "news.js",
    "news-ticker.js",
    "dbr-mark.svg",
    "photo_2026-09-29_14-04-02.jpg",
)
THUMBNAIL_ENDPOINT = "https://thumbnails.roblox.com/v1/users/avatar-headshot"


def read_staff():
    with (ROOT / "data" / "staff.json").open(encoding="utf-8") as source:
        staff = json.load(source)
    if not isinstance(staff, list):
        raise ValueError("data/staff.json must contain a JSON array")
    return staff


def roblox_headshot(user_id):
    url = f"{THUMBNAIL_ENDPOINT}?userIds={user_id}&size=180x180&format=Png&isCircular=false"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "DBR-RP-Pages/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Could not resolve avatar for Roblox ID {user_id}: {error}")
        return None

    records = payload.get("data", [])
    image_url = records[0].get("imageUrl") if records and records[0].get("state") == "Completed" else None
    if not image_url:
        return None
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not (parsed.hostname == "rbxcdn.com" or parsed.hostname.endswith(".rbxcdn.com")):
        print(f"Ignored non-Roblox avatar URL for Roblox ID {user_id}")
        return None
    return image_url


def build():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    for filename in PUBLIC_FILES:
        shutil.copy2(ROOT / filename, OUTPUT / filename)

    (OUTPUT / "pages-config.json").write_text('{"static": true}\n', encoding="utf-8")
    (OUTPUT / "data").mkdir()
    shutil.copy2(ROOT / "data" / "news.json", OUTPUT / "data" / "news.json")

    staff = read_staff()
    for employee in staff:
        user_id = employee.get("roblox_user_id")
        if not isinstance(user_id, int) or user_id < 1:
            raise ValueError(f"Invalid roblox_user_id in staff record: {employee!r}")
        employee.setdefault("profile_url", f"https://www.roblox.com/users/{user_id}/profile")
        employee["avatar_url"] = roblox_headshot(user_id) or employee.get("avatar_url", "")

    with (OUTPUT / "data" / "staff.json").open("w", encoding="utf-8", newline="\n") as target:
        json.dump(staff, target, ensure_ascii=False, indent=2)
        target.write("\n")

    (OUTPUT / ".nojekyll").touch()
    print(f"Built static GitHub Pages site in {OUTPUT}")
    print("Excluded: Flask admin, SQLite database, and Python source files")


if __name__ == "__main__":
    build()
