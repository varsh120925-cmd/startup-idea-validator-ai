import unittest
from agents.idea_extractor import IdeaExtractionAgent
from agents.market_analyzer import MarketAnalyzerAgent
from agents.competitor_agent import CompetitorDiscoveryAgent
from agents.swot_risk_agent import SWOTRiskAgent
from agents.mvp_recommender import MVPRecommenderAgent
from agents.gtm_strategist import GTMStrategistAgent
from agents.startup_advisor import StartupAdvisorAgent
from agents.report_generator import ReportGeneratorAgent

class AgentsTestCase(unittest.TestCase):
    def setUp(self):
        self.sample_context = {
            "title": "LexiDraft AI",
            "raw_description": "An AI assistant that reviews freelance software developer contracts and flags dangerous indemnification terms.",
            "industry": "LegalTech / Productivity SaaS"
        }

    def test_agent_1_idea_extractor(self):
        agent = IdeaExtractionAgent()
        res = agent.run(self.sample_context)
        self.assertIn("business_concept", res)
        self.assertIn("problem_statement", res)
        self.assertIn("proposed_solution", res)
        self.assertIn("target_audience", res)
        self.assertIn("_meta", res)

    def test_agent_2_market_analyzer(self):
        agent = MarketAnalyzerAgent()
        ctx = dict(self.sample_context)
        ctx["extractor_data"] = {"industry": "LegalTech", "problem_statement": "Bad contracts"}
        res = agent.run(ctx)
        self.assertIn("tam", res)
        self.assertIn("sam", res)
        self.assertIn("som", res)
        self.assertIn("cagr", res)
        self.assertIn("customer_segments", res)

    def test_agent_3_competitor_discovery(self):
        agent = CompetitorDiscoveryAgent()
        ctx = dict(self.sample_context)
        ctx["extractor_data"] = {"proposed_solution": "Contract analysis", "problem_statement": "Contracts"}
        res = agent.run(ctx)
        self.assertIn("competitors", res)
        self.assertGreater(len(res["competitors"]), 0)
        self.assertIn("defensibility_score", res)

    def test_agent_4_swot_risk(self):
        agent = SWOTRiskAgent()
        ctx = dict(self.sample_context)
        ctx["extractor_data"] = {"industry": "LegalTech"}
        res = agent.run(ctx)
        self.assertIn("swot", res)
        self.assertIn("strengths", res["swot"])
        self.assertIn("risks", res)
        self.assertIn("overall_risk_score", res)

    def test_agent_5_mvp_recommender(self):
        agent = MVPRecommenderAgent()
        ctx = dict(self.sample_context)
        ctx["extractor_data"] = {"proposed_solution": "AI contract reviewer"}
        res = agent.run(ctx)
        self.assertIn("must_have", res)
        self.assertIn("should_have", res)
        self.assertIn("effort_vs_impact", res)
        self.assertIn("estimated_mvp_weeks", res)

    def test_agent_6_gtm_strategist(self):
        agent = GTMStrategistAgent()
        ctx = dict(self.sample_context)
        ctx["extractor_data"] = {"industry": "LegalTech", "target_audience": "Freelancers"}
        res = agent.run(ctx)
        self.assertIn("positioning_statement", res)
        self.assertIn("ideal_customer_profile", res)
        self.assertIn("pricing_strategy", res)
        self.assertIn("launch_roadmap_90_days", res)

    def test_agent_7_advisor_chatbot(self):
        advisor = StartupAdvisorAgent()
        reply_dict = advisor.answer_query(
            user_query="How do I acquire my first 100 customers?",
            idea_dict={"title": "LexiDraft AI", "industry": "LegalTech", "viability_score": 82},
            analysis_dict={}
        )
        self.assertEqual(reply_dict["status"], "success")
        self.assertIn("reply", reply_dict)
        self.assertTrue(len(reply_dict["reply"]) > 50)

        # Test pipeline execution mode
        exec_res = advisor.run(dict(self.sample_context))
        self.assertIn("advisory_summary", exec_res)
        self.assertIn("top_strategic_recommendations", exec_res)
        self.assertIn("first_100_customers_playbook", exec_res)

    def test_agent_8_report_generator(self):
        agent = ReportGeneratorAgent()
        res = agent.run({"idea": self.sample_context, "analysis_dict": {}})
        self.assertIn("executive_summary", res)
        self.assertIn("viability_score", res)
        self.assertIn("recommendation", res)
        self.assertIn(res["recommendation"], ["PROCEED", "IMPROVE", "RECONSIDER"])
        self.assertIn("biggest_strength", res)
        self.assertIn("biggest_weakness", res)
        self.assertIn("best_market_opportunity", res)
        self.assertIn("recommended_next_action", res)
        self.assertGreater(res["viability_score"], 0)

if __name__ == "__main__":
    unittest.main()
