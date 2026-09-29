import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as dbr_app


class StaffApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_database_path = dbr_app.DATABASE_PATH
        self.old_news_path = dbr_app.NEWS_DATA_PATH
        self.old_admin_token = dbr_app.ADMIN_TOKEN
        self.old_resolver = dbr_app.resolve_roblox_user
        dbr_app.DATABASE_PATH = Path(self.temp_dir.name) / "test.sqlite3"
        dbr_app.NEWS_DATA_PATH = Path(self.temp_dir.name) / "news.json"
        dbr_app.NEWS_DATA_PATH.write_text("[]\n", encoding="utf-8")
        dbr_app.ADMIN_TOKEN = "test-admin-token"
        dbr_app.resolve_roblox_user = lambda username: {
            "id": 101 if username.lower() == "alpha" else 202,
            "name": username,
            "displayName": f"{username} RP",
        }
        dbr_app.initialize_db()
        dbr_app.app.config.update(TESTING=True)
        self.client = dbr_app.app.test_client()
        self.headers = {"Authorization": "Bearer test-admin-token"}

    def tearDown(self):
        dbr_app.DATABASE_PATH = self.old_database_path
        dbr_app.NEWS_DATA_PATH = self.old_news_path
        dbr_app.ADMIN_TOKEN = self.old_admin_token
        dbr_app.resolve_roblox_user = self.old_resolver
        self.temp_dir.cleanup()

    def payload(self, username="Alpha", rank="Курсант"):
        return {
            "username": username,
            "rank": rank,
            "department": "ТСВ",
            "call_sign": "Оріон-01",
        }

    def test_writes_require_admin_token(self):
        response = self.client.post("/api/staff", json=self.payload())
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get("/api/staff").json, [])

    def test_admin_options_include_leadership_ranks_and_real_departments(self):
        options = self.client.get("/api/config").json
        self.assertEqual(options["ranks"][-2:], ["Заступник Директора ДБР", "Директор ДБР"])
        self.assertEqual(options["departments"], ["ТСВ", "ОСД"])

    def test_news_page_and_local_data_routes_are_available(self):
        for path in ("/news.html", "/news.js"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            response.close()

        news_data = self.client.get("/data/news.json")
        self.assertEqual(news_data.json, [])
        news_data.close()
        self.assertEqual(self.client.get("/pages-config.json").json, {"static": False})

    def test_admin_can_add_list_and_delete_news(self):
        payload = {
            "date": "2026-09-29",
            "category": "Оголошення",
            "title": "Тестова новина",
            "summary": "Короткий опис",
            "content": "Перший абзац.\nДругий абзац.",
        }
        unauthorized = self.client.post("/api/news", json=payload)
        self.assertEqual(unauthorized.status_code, 401)

        created = self.client.post("/api/news", json=payload, headers=self.headers)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["content"], ["Перший абзац.", "Другий абзац."])
        self.assertEqual(self.client.get("/api/admin/news", headers=self.headers).json[0]["title"], "Тестова новина")

        deleted = self.client.delete(f"/api/news/{created.json['id']}", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/admin/news", headers=self.headers).json, [])

    def test_add_edit_list_and_delete_staff(self):
        created = self.client.post("/api/staff", json=self.payload(), headers=self.headers)
        self.assertEqual(created.status_code, 201)
        employee_id = created.json["id"]
        self.assertEqual(created.json["roblox_user_id"], 101)
        self.assertEqual(created.json["display_name"], "Alpha RP")
        self.assertEqual(len(self.client.get("/api/staff").json), 1)

        updated = self.client.put(
            f"/api/staff/{employee_id}",
            json=self.payload(username="Bravo", rank="Капрал"),
            headers=self.headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["username"], "Bravo")
        self.assertEqual(updated.json["rank"], "Капрал")

        deleted = self.client.delete(f"/api/staff/{employee_id}", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/staff").json, [])

    def test_duplicate_roblox_user_is_rejected(self):
        first = self.client.post("/api/staff", json=self.payload(), headers=self.headers)
        second = self.client.post("/api/staff", json=self.payload(), headers=self.headers)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)

    def test_headshot_uses_official_roblox_thumbnail_and_rejects_external_hosts(self):
        with patch.object(
            dbr_app,
            "fetch_json",
            return_value={"data": [{"state": "Completed", "imageUrl": "https://tr.rbxcdn.com/avatar.png"}]},
        ):
            accepted = self.client.get("/api/avatar/101/headshot")
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(accepted.headers["Location"], "https://tr.rbxcdn.com/avatar.png")

        with patch.object(
            dbr_app,
            "fetch_json",
            return_value={"data": [{"state": "Completed", "imageUrl": "https://rbxcdn.com.attacker.test/avatar.png"}]},
        ):
            rejected = self.client.get("/api/avatar/101/headshot")
        self.assertEqual(rejected.status_code, 502)


if __name__ == "__main__":
    unittest.main()
