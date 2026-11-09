import unittest
import os
import tempfile
from config import Config

class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        Config.DATABASE_PATH = self.temp_db.name

        from database.db import init_db
        init_db()

    def tearDown(self):
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_user_creation_and_auth(self):
        from database.models import User
        user = User.create("testfounder", "test@venture.com", "securepass123", "Test Founder")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testfounder")
        self.assertTrue(user.check_password("securepass123"))
        self.assertFalse(user.check_password("wrongpass"))

        by_email = User.get_by_email("TEST@VENTURE.COM")
        self.assertIsNotNone(by_email)
        self.assertEqual(by_email.id, user.id)

    def test_startup_idea_crud(self):
        from database.models import User, StartupIdea
        user = User.create("ideauser", "idea@venture.com", "pass123")
        idea_id = StartupIdea.create(
            user_id=user.id,
            title="AI Code Reviewer",
            raw_description="Automated code review bot for pull requests",
            industry="Developer Tools"
        )
        self.assertGreater(idea_id, 0)

        idea = StartupIdea.get_by_id(idea_id)
        self.assertEqual(idea["title"], "AI Code Reviewer")
        self.assertEqual(idea["status"], "draft")

        StartupIdea.update_status(idea_id, "completed", viability_score=84, recommendation="Strong Pursue")
        updated = StartupIdea.get_by_id(idea_id)
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["viability_score"], 84)

        stats = StartupIdea.get_user_stats(user.id)
        self.assertEqual(stats["total_ideas"], 1)
        self.assertEqual(stats["completed_validations"], 1)
        self.assertEqual(stats["high_potential"], 1)

    def test_competitor_batch_save(self):
        from database.models import User, StartupIdea, Competitor
        user = User.create("compuser", "comp@venture.com", "pass123")
        idea_id = StartupIdea.create(user.id, "Title", "Desc")

        comps = [
            {"name": "Comp1", "competitor_type": "Direct", "pricing_model": "$50/mo", "market_gap": "Better UI"},
            {"name": "Comp2", "competitor_type": "Indirect", "pricing_model": "Freemium", "market_gap": "Cheaper"}
        ]
        Competitor.save_batch(idea_id, comps)
        fetched = Competitor.get_by_idea(idea_id)
        self.assertEqual(len(fetched), 2)
        self.assertEqual(fetched[0]["name"], "Comp1")

if __name__ == "__main__":
    unittest.main()
