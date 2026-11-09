import json
from .base_agent import BaseAgent

class MarketAnalyzerAgent(BaseAgent):
    """Agent 2: Evaluates market size (TAM/SAM/SOM), growth trends, and customer segmentation"""

    def __init__(self):
        super().__init__(
            name="market",
            description="Analyzes market size, demand, industry trends, customer personas, and growth opportunities."
        )

    def _execute_llm(self, context):
        extractor_data = context.get("extractor_data", {})
        title = context.get("title", "")
        industry = extractor_data.get("industry") or context.get("industry", "Technology")
        problem = extractor_data.get("problem_statement", "")
        audience = extractor_data.get("target_audience", "")

        # Retrieve live search trends
        search_query = f"{industry} market size growth CAGR trends 2025 2026 {title}"
        search_results = self.search_service.search(search_query, max_results=3)

        web_context_str = "\n".join([f"- [{s.get('title')}]: {s.get('snippet')} ({s.get('url')})" for s in search_results])

        system_prompt = (
            "You are a Principal Market Research Analyst and Venture Capital Partner. "
            "Analyze market sizing, CAGR growth, customer segmentation personas, and macro trends. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Evaluate the market opportunity for this startup:
Title: {title}
Industry: {industry}
Target Audience: {audience}
Problem Statement: {problem}

Live Web Research Context:
{web_context_str}

Return a valid JSON object with the following exact keys:
{{
  "tam": "estimated Total Addressable Market (e.g. $14.8 Billion)",
  "tam_numeric_billions": 14.8,
  "sam": "estimated Serviceable Addressable Market (e.g. $3.2 Billion)",
  "sam_numeric_billions": 3.2,
  "som": "estimated Serviceable Obtainable Market for early years (e.g. $160 Million)",
  "som_numeric_millions": 160.0,
  "cagr": "expected market growth rate percentage (e.g. 15.4%)",
  "market_demand_level": "High" or "Moderate" or "Emerging",
  "market_drivers": ["driver 1", "driver 2", "driver 3"],
  "industry_trends": [
    {{"trend": "trend title", "impact": "explanation of impact"}},
    {{"trend": "trend title", "impact": "explanation of impact"}}
  ],
  "customer_segments": [
    {{
      "segment_name": "Primary Segment Name",
      "persona": "Description of the typical buyer / decision maker",
      "pain_point": "Their primary unresolved friction",
      "willingness_to_pay": "High / Medium / Low ($XX/mo)",
      "acquisition_channel": "Best channel to reach them"
    }},
    {{
      "segment_name": "Secondary Segment Name",
      "persona": "Description of secondary segment",
      "pain_point": "Their secondary friction",
      "willingness_to_pay": "Medium / Low ($XX/mo)",
      "acquisition_channel": "Best channel to reach them"
    }}
  ],
  "unmet_needs": ["Unmet need 1", "Unmet need 2"],
  "research_sources": {json.dumps(search_results)}
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.groq_service.chat_completion(messages, temperature=0.4, json_mode=True)

    def _execute_fallback(self, context):
        extractor_data = context.get("extractor_data", {})
        industry = extractor_data.get("industry") or context.get("industry", "B2B SaaS")
        title = context.get("title", "Startup Platform")
        problem = extractor_data.get("problem_statement", "Market friction")
        audience = extractor_data.get("target_audience", "Businesses and professionals")

        # Get web context (simulated / real depending on key)
        search_results = self.search_service.search_market_trends(industry, title)

        return {
            "tam": "$18.6 Billion",
            "tam_numeric_billions": 18.6,
            "sam": "$4.2 Billion",
            "sam_numeric_billions": 4.2,
            "som": "$210 Million",
            "som_numeric_millions": 210.0,
            "cagr": "16.8%",
            "market_demand_level": "High",
            "market_drivers": [
                f"Accelerated transition to automated workflows in {industry}",
                "Growing enterprise and SMB willingness to pay for specialized vertical software",
                "Pressure to cut operational overhead and manual administrative labor"
            ],
            "industry_trends": [
                {
                    "trend": "AI-Powered Copilot Integration",
                    "impact": "End-users now expect domain-specific generative recommendations rather than raw static tools."
                },
                {
                    "trend": "Unbundling of Bloated Enterprise Software",
                    "impact": "Modern buyers favor purpose-built, agile platforms with rapid time-to-value over monolithic suites."
                },
                {
                    "trend": "Self-Serve & Usage-Based Pricing Transparency",
                    "impact": "Reduced buyer friction by offering transparent entry pricing and frictionless trials."
                }
            ],
            "customer_segments": [
                {
                    "segment_name": "Agile Early Adopters & Operators",
                    "persona": f"Forward-thinking leads directly feeling the pain of '{problem[:60]}...'",
                    "pain_point": "Excessive manual hours wasted on fragmented tasks without unified oversight.",
                    "willingness_to_pay": "High ($49 - $199/month)",
                    "acquisition_channel": "Niche online communities, LinkedIn targeted thought leadership, Product Hunt"
                },
                {
                    "segment_name": "Growing Mid-Market Organizations",
                    "persona": "Department heads and VP/Directors needing standardized, compliant processes.",
                    "pain_point": "Lack of team standardization, audit trails, and consistent throughput quality.",
                    "willingness_to_pay": "Very High ($500 - $2,500/month)",
                    "acquisition_channel": "Direct B2B account-based outbound, webinars, and partner ecosystems"
                }
            ],
            "unmet_needs": [
                "Zero-friction onboarding without lengthy IT integration cycles",
                "Built-in actionable recommendations rather than raw dashboards",
                "Collaborative team workflows with exportable audit logs"
            ],
            "research_sources": search_results
        }
