import unittest
import os
import tempfile
import json
from config import Config
from app import create_app
from database.db import init_db
from database.models import User, StartupIdea
from orchestration.pipeline import OrchestrationPipeline

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        Config.DATABASE_PATH = self.temp_db.name

        self.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            self.user = User.create("testroute", "route@venture.com", "pass123")
            self.idea_id = StartupIdea.create(
                user_id=self.user.id,
                title="RouteTest SaaS",
                raw_description="Route testing platform",
                industry="B2B SaaS"
            )
            # Run pipeline to populate all agent analyses for this idea
            pipeline = OrchestrationPipeline(idea_id=self.idea_id, user_id=self.user.id)
            pipeline.run_synchronous()

    def tearDown(self):
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def _login(self):
        return self.client.post("/login", data={"email": "route@venture.com", "password": "pass123"}, follow_redirects=True)

    def test_auth_routes(self):
        # GET Login
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)

        # GET Register
        res = self.client.get("/register")
        self.assertEqual(res.status_code, 200)

        # Demo Login
        res = self.client.get("/demo-login", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dashboard", res.data)

    def test_all_13_pages_accessible(self):
        self._login()

        pages = [
            ("/dashboard", "Page 2: Main Dashboard"),
            ("/submit", "Page 3: Startup Idea Submission"),
            (f"/idea/{self.idea_id}/market", "Page 4: Market Opportunity Analysis"),
            (f"/idea/{self.idea_id}/competitors", "Page 5: Competitor Analysis"),
            (f"/idea/{self.idea_id}/swot", "Page 6: SWOT Analysis"),
            (f"/idea/{self.idea_id}/risks", "Page 7: Risk Analysis"),
            (f"/idea/{self.idea_id}/mvp", "Page 8: MVP Feature Recommendations"),
            (f"/idea/{self.idea_id}/gtm", "Page 9: Go-to-Market Strategy"),
            (f"/idea/{self.idea_id}/chat", "Page 10: AI Startup Advisor Chatbot"),
            ("/history", "Page 11: Validation History"),
            (f"/idea/{self.idea_id}/report", "Page 12: Final Report Generation"),
            ("/settings", "Page 13: Settings & Profile")
        ]

        for url, page_name in pages:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"Failed accessing {page_name} at {url}")

    def test_api_chat_endpoint(self):
        self._login()
        res = self.client.post(
            f"/api/idea/{self.idea_id}/chat",
            data=json.dumps({"message": "How do I price my product?"}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("reply", data)

    def test_export_pdf_endpoint(self):
        self._login()
        res = self.client.get(f"/api/export/{self.idea_id}/pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")

    def test_export_json_endpoint(self):
        self._login()
        res = self.client.get(f"/api/export/{self.idea_id}/json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/json")
        data = json.loads(res.data)
        self.assertIn("startup_idea", data)
        self.assertIn("analyses", data)

    def test_export_markdown_endpoint(self):
        self._login()
        res = self.client.get(f"/api/export/{self.idea_id}/markdown")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"# Startup Validation Report", res.data)

    def test_export_csv_endpoint(self):
        self._login()
        res = self.client.get(f"/api/export/{self.idea_id}/csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")
        self.assertIn(b"STARTUP IDEA VALIDATION REPORT", res.data)
        self.assertIn(b"COMPETITOR COMPARISON TABLE", res.data)
        self.assertIn(b"6-WEEK MVP DEVELOPMENT ROADMAP", res.data)

    def test_api_idea_status_with_verdict(self):
        self._login()
        res = self.client.get(f"/api/idea/{self.idea_id}/status")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("verdict", data)
        self.assertIn("progress", data)
        self.assertIn("agents", data["progress"])
        verdict = data["verdict"]
        self.assertIn(verdict["recommendation"], ["PROCEED", "IMPROVE", "RECONSIDER"])
        self.assertIn("biggest_strength", verdict)
        self.assertIn("biggest_weakness", verdict)
        self.assertIn("best_market_opportunity", verdict)
        self.assertIn("recommended_next_action", verdict)

    def test_api_ideas_compare_endpoint(self):
        self._login()
        with self.app.app_context():
            idea2_id = StartupIdea.create(
                user_id=self.user.id,
                title="Second Concept AI",
                raw_description="Alternative startup idea",
                industry="LegalTech"
            )
            p2 = OrchestrationPipeline(idea_id=idea2_id, user_id=self.user.id)
            p2.run_synchronous()

        res = self.client.get(f"/api/ideas/compare?id1={self.idea_id}&id2={idea2_id}")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("idea1", data)
        self.assertIn("idea2", data)
        self.assertIn("verdict", data["idea1"])
        self.assertIn("verdict", data["idea2"])

if __name__ == "__main__":
    unittest.main()
