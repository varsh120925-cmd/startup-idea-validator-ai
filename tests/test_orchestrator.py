import unittest
import os
import tempfile
from config import Config
from database.db import init_db
from database.models import User, StartupIdea, AnalysisResult, Competitor, ValidationReport
from orchestration.pipeline import OrchestrationPipeline

class OrchestratorTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        Config.DATABASE_PATH = self.temp_db.name
        init_db()

        self.user = User.create("testorch", "orch@venture.com", "pass123")
        self.idea_id = StartupIdea.create(
            user_id=self.user.id,
            title="CleanTrace Cloud",
            raw_description="Automated environmental compliance tracking for mid-market suppliers",
            industry="ClimateTech"
        )

    def tearDown(self):
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_pipeline_execution_synchronous(self):
        pipeline = OrchestrationPipeline(idea_id=self.idea_id, user_id=self.user.id)
        result = pipeline.run_synchronous()

        self.assertEqual(result["status"], "completed")
        self.assertGreater(result["viability_score"], 50)
        self.assertIsNotNone(result["pdf_filename"])

        # Check DB updates
        updated_idea = StartupIdea.get_by_id(self.idea_id)
        self.assertEqual(updated_idea["status"], "completed")
        self.assertEqual(updated_idea["viability_score"], result["viability_score"])

        # Verify all agent results were stored
        all_analyses = AnalysisResult.get_all_for_idea(self.idea_id)
        for agent_name in ["extractor", "market", "competitors", "swot_risk", "mvp", "gtm", "report"]:
            self.assertIn(agent_name, all_analyses)
            self.assertIn("data", all_analyses[agent_name])

        # Verify competitors were saved
        comps = Competitor.get_by_idea(self.idea_id)
        self.assertGreater(len(comps), 0)

        # Verify validation report record was created
        report = ValidationReport.get_by_idea(self.idea_id)
        self.assertIsNotNone(report)
        self.assertEqual(report["viability_score"], result["viability_score"])

if __name__ == "__main__":
    unittest.main()
