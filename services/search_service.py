import os
import json
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class SearchService:
    """Service to perform web search using Tavily API with graceful fallback"""

    TAVILY_ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key=None):
        self.api_key = api_key or Config.TAVILY_API_KEY

    def is_available(self):
        return bool(self.api_key and len(self.api_key.strip()) > 8)

    def test_connection(self):
        """Test Tavily API key connectivity"""
        if not self.is_available():
            return False, "Tavily API Key is not set or empty."
        try:
            res = requests.post(
                self.TAVILY_ENDPOINT,
                json={"api_key": self.api_key, "query": "startup market trends", "max_results": 1},
                timeout=8
            )
            if res.status_code == 200:
                return True, "Tavily API connected successfully!"
            return False, f"Tavily returned HTTP {res.status_code}: {res.text[:120]}"
        except Exception as e:
            return False, f"Tavily connection error: {str(e)}"

    def search(self, query, max_results=5, search_depth="basic"):
        """
        Execute web search via Tavily API.
        Returns list of search result dicts with url, title, snippet, source_type.
        """
        if self.is_available():
            try:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False
                }
                res = requests.post(self.TAVILY_ENDPOINT, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title", "Market Research"),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "source_type": "Verified Web Research (Tavily Live)",
                            "is_verified": True
                        })
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"Tavily live search error for query '{query}': {e}. Using simulated intelligence fallback.")

        # Realistic Domain-Aware Research Fallback when API key is missing or failed
        return self._generate_simulated_search_results(query)

    def search_competitors(self, industry, product_concept):
        """Dedicated competitor research query"""
        query = f"top competitors and alternatives for {product_concept} in {industry} software companies"
        return self.search(query, max_results=5)

    def search_market_trends(self, industry, domain):
        """Dedicated market growth and trends query"""
        query = f"{industry} {domain} market size growth CAGR industry trends report 2025 2026"
        return self.search(query, max_results=4)

    def _generate_simulated_search_results(self, query):
        """
        Generates realistic domain-relevant web references clearly labelled as
        Simulated Market Intelligence (Demo Mode) to prevent hallucination without live API.
        """
        q = query.lower()
        if "competitor" in q or "alternative" in q:
            return [
                {
                    "title": "G2 Software Reviews & Category Leaders",
                    "url": "https://www.g2.com/categories",
                    "snippet": "Analysis of leading category incumbents showing high demand for automation, self-serve onboarding, and transparent pricing in this sector.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                },
                {
                    "title": "TechCrunch Venture & Startup Landscape",
                    "url": "https://techcrunch.com/startups",
                    "snippet": "Venture capital deal activity indicates active interest in modern verticalized workflows, AI copilots, and cost-reduction tooling.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                },
                {
                    "title": "Product Hunt Trending Launches",
                    "url": "https://www.producthunt.com/topics",
                    "snippet": "Recent indie hacker launches indicate strong user friction around complex setups, creating an opening for lightweight, focused solutions.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                }
            ]
        else:
            return [
                {
                    "title": "Grand View Research - Global Market Report",
                    "url": "https://www.grandviewresearch.com/industry-analysis",
                    "snippet": "The global market is expanding at an estimated 14.8% CAGR driven by cloud adoption, digital operations, and demand for AI-assisted workflows.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                },
                {
                    "title": "Gartner Technology Trends & Hype Cycle",
                    "url": "https://www.gartner.com/en/research",
                    "snippet": "Enterprise and SMB buyers are consolidating specialized tools into integrated suites that deliver measurable ROI within 90 days.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                },
                {
                    "title": "Statista Industry Market Outlook",
                    "url": "https://www.statista.com/outlook",
                    "snippet": "Customer segment spending shows steady double-digit budget allocation increases for efficiency-boosting automated software.",
                    "source_type": "Simulated Market Research (Demo Mode)",
                    "is_verified": False
                }
            ]
