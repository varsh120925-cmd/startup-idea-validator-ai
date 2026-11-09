import unittest
import os
import tempfile
from services.pdf_service import PDFReportService

class PDFReportTestCase(unittest.TestCase):
    def test_pdf_generation_bytes_and_file(self):
        sample_idea = {
            "id": 999,
            "title": "FinSight Analytics",
            "industry": "FinTech / SaaS",
            "viability_score": 85,
            "recommendation": "Strong Pursue",
            "problem_statement": "Manual reconciliation takes 15 hours weekly",
            "proposed_solution": "Real-time automated reconciliation engine"
        }
        sample_analyses = {
            "extractor": {
                "data": {
                    "problem_statement": sample_idea["problem_statement"],
                    "proposed_solution": sample_idea["proposed_solution"],
                    "target_audience": "CFOs & Finance teams",
                    "revenue_model": "Subscription"
                }
            },
            "market": {
                "data": {
                    "tam": "$10 Billion",
                    "sam": "$2 Billion",
                    "som": "$100 Million",
                    "cagr": "14.5%",
                    "customer_segments": [{"segment_name": "Mid-Market", "pain_point": "Reconciliation delay"}]
                }
            },
            "swot_risk": {
                "data": {
                    "swot": {
                        "strengths": ["Fast API"],
                        "weaknesses": ["Brand presence"],
                        "opportunities": ["Open banking"],
                        "threats": ["Bank APIs"]
                    },
                    "risks": [{"category": "Technical", "severity": "Medium", "risk": "API lag", "mitigation": "Retry queues"}]
                }
            },
            "mvp": {
                "data": {
                    "must_have": ["Bank CSV ingestion", "Discrepancy alerts"]
                }
            },
            "gtm": {
                "data": {
                    "acquisition_channels": ["LinkedIn Outbound", "Accounting Partner Program"]
                }
            }
        }
        sample_competitors = [
            {"name": "LegacyCorp", "competitor_type": "Direct", "weaknesses": "High cost", "market_gap": "Automated reconciliation"}
        ]

        # Test buffer generation
        pdf_bytes = PDFReportService.generate_report(
            idea=sample_idea,
            analysis_dict=sample_analyses,
            competitors=sample_competitors
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        # Test disk file generation
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            PDFReportService.generate_report(
                idea=sample_idea,
                analysis_dict=sample_analyses,
                competitors=sample_competitors,
                output_path=temp_path
            )
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 1000)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
