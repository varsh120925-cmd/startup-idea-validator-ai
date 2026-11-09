import json
from .base_agent import BaseAgent

class SWOTRiskAgent(BaseAgent):
    """Agent 4: Conducts comprehensive SWOT analysis and categorized risk matrix with actionable mitigations"""

    def __init__(self):
        super().__init__(
            name="swot_risk",
            description="Evaluates internal/external SWOT factors, calculates risk severity, and creates tactical mitigation plans."
        )

    def _execute_llm(self, context):
        extractor_data = context.get("extractor_data", {})
        market_data = context.get("market_data", {})
        competitor_data = context.get("competitor_data", {})
        title = context.get("title", "")
        industry = extractor_data.get("industry", "Technology")

        system_prompt = (
            "You are a Venture Capital Due Diligence Director and Risk Management Expert. "
            "Analyze the startup proposition, market dynamics, and competitive threats. "
            "Produce an actionable SWOT matrix and rigorous categorized risk assessment. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Analyze SWOT and Risks for:
Title: {title}
Industry: {industry}
Business Concept: {extractor_data.get('business_concept', '')}
Value Proposition: {extractor_data.get('unique_value_proposition', '')}
Market TAM/CAGR: {market_data.get('tam', '')} / {market_data.get('cagr', '')}
Defensibility: {competitor_data.get('defensibility_score', 75)}/100

Return a valid JSON object with the following exact keys:
{{
  "swot": {{
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
    "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
    "threats": ["threat 1", "threat 2", "threat 3"]
  }},
  "risks": [
    {{
      "category": "Market" or "Technical" or "Financial" or "Business Model" or "Regulatory",
      "risk": "Description of the specific risk",
      "severity": "High" or "Medium" or "Low",
      "impact_score": 7,
      "likelihood_score": 5,
      "mitigation": "Practical, step-by-step mitigation strategy"
    }}
  ],
  "overall_risk_score": 38,
  "risk_rating": "Low Risk" or "Moderate Risk" or "High Risk",
  "founder_advice": "Key cautionary piece of advice for the founder"
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.groq_service.chat_completion(messages, temperature=0.3, json_mode=True)

    def _execute_fallback(self, context):
        extractor_data = context.get("extractor_data", {})
        title = context.get("title", "Startup Platform")
        industry = extractor_data.get("industry", "B2B SaaS")

        return {
            "swot": {
                "strengths": [
                    "High agility and zero legacy architectural debt compared to incumbents",
                    "Domain-specific AI workflow delivering immediate tangible time savings",
                    "Lower cost structure enabling accessible self-serve pricing"
                ],
                "weaknesses": [
                    "Early brand recognition and unproven market presence",
                    "Initial cold-start challenge in collecting proprietary training telemetry",
                    "Limited early capital reserves requiring disciplined runway management"
                ],
                "opportunities": [
                    f"Strong secular growth in {industry} with expanding budget allocations",
                    "Opportunity to build a proprietary workflow integration ecosystem",
                    "Potential to expand into international markets and adjacent vertical niches"
                ],
                "threats": [
                    "Incumbents rapidly rolling out lightweight copilot features into existing tools",
                    "Rising paid acquisition costs across traditional digital ad channels",
                    "Evolving data privacy, compliance, and regulatory frameworks"
                ]
            },
            "risks": [
                {
                    "category": "Market",
                    "risk": "Customer inertia and reluctance to change existing default habits.",
                    "severity": "Medium",
                    "impact_score": 7,
                    "likelihood_score": 5,
                    "mitigation": "Offer frictionless 14-day free trials with pre-populated demo environments and 1-click data imports."
                },
                {
                    "category": "Business Model",
                    "risk": "Customer Acquisition Cost (CAC) exceeding Customer Lifetime Value (LTV) during early scaling.",
                    "severity": "High",
                    "impact_score": 8,
                    "likelihood_score": 6,
                    "mitigation": "Prioritize high-converting organic channels, content SEO, and viral referral loops before deploying heavy paid ad budgets."
                },
                {
                    "category": "Technical",
                    "risk": "Dependency on third-party LLM APIs for latency, costs, and availability.",
                    "severity": "Medium",
                    "impact_score": 6,
                    "likelihood_score": 4,
                    "mitigation": "Implement model-agnostic abstraction layers, aggressive prompt caching, and fallback open-source model routing."
                },
                {
                    "category": "Regulatory",
                    "risk": "Data protection, GDPR/CCPA compliance, and intellectual property ownership concerns.",
                    "severity": "Low",
                    "impact_score": 5,
                    "likelihood_score": 3,
                    "mitigation": "Enforce strict zero-data retention policies for customer inputs and secure SOC2 / ISO compliance roadmaps early."
                }
            ],
            "overall_risk_score": 36,
            "risk_rating": "Moderate Risk",
            "founder_advice": f"Your primary risk is not technical execution, but distribution velocity. Focus ruthlessly on locking in your first 25 reference customer case studies."
        }
