import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = patch.object(app, "DATA_FILE", Path(self.temp.name) / "data" / "state.json")
        self.state.start()
        self.client = TestClient(app.app)

    def tearDown(self):
        self.client.close()
        self.state.stop()
        self.temp.cleanup()

    def email(self, **changes):
        data = dict(id=1, sender="Friend", subject="Hello", body="See you tomorrow.", received="2026-09-19T12:00")
        data.update(changes)
        return app.EmailItem(**data)

    def test_priority(self):
        self.assertEqual(app.classify(self.email(subject="Interview"))[0], "high")
        self.assertEqual(app.classify(self.email(subject="Assignment"))[0], "medium")
        self.assertEqual(app.classify(self.email(subject="Newsletter sale"))[0], "low")
        self.assertEqual(app.classify(self.email(body="An overdue television purchase."))[0], "low")

    def test_summary(self):
        self.assertEqual(app.clean_summary("  hello   world  "), "hello world")
        self.assertEqual(app.clean_summary("one two three", 2), "one two...")

    def test_empty_dashboard(self):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["emails"], [])

    def test_reset_demo(self):
        self.assertEqual(self.client.post("/api/demo/reset").status_code, 200)
        data = self.client.get("/api/dashboard").json()
        self.assertEqual(len(data["emails"]), 4)
        self.assertEqual(sum(data["counts"].values()), 4)
        self.assertEqual(len(data["calendar"]), 2)

    def test_order_and_past_events(self):
        app.save_state({"emails": [
            self.email(id=1, subject="Interview", received="2026-09-18T12:00").model_dump(),
            self.email(id=2, subject="Interview", received="2026-09-19T12:00").model_dump(),
            self.email(id=3, received="2026-09-20T12:00").model_dump()],
            "calendar": [{"id": 1, "title": "Old", "start": "2000-01-01T12:00"}]})
        data = self.client.get("/api/dashboard").json()
        self.assertEqual([e["id"] for e in data["emails"]], [2, 1, 3])
        self.assertEqual(data["calendar"], [])

    def test_analyze_and_validation(self):
        response = self.client.post("/api/analyze", json=self.email(subject="Interview").model_dump())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["priority"], "high")
        self.assertEqual(self.client.post("/api/analyze", json={}).status_code, 422)

    def test_connections_are_not_faked(self):
        data = self.client.get("/api/connections").json()
        self.assertTrue(all(not item["connected"] for item in data.values()))

    def test_static_routes(self):
        for path in ["/", "/manifest.webmanifest", "/sw.js", "/static/app.js", "/static/style.css",
                     "/static/icons/icon-192.png", "/static/icons/icon-512.png"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


if __name__ == "__main__":
    unittest.main()
