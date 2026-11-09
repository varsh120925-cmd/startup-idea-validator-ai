import json
from .base_agent import BaseAgent

class CompetitorDiscoveryAgent(BaseAgent):
    """Agent 3: Discovers direct and indirect competitors via web research and identifies strategic market gaps"""

    def __init__(self):
        super().__init__(
            name="competitors",
            description="Discovers competitors, analyzes pricing, strengths, weaknesses, and maps actionable market gaps."
        )

    def _execute_llm(self, context):
        extractor_data = context.get("extractor_data", {})
        title = context.get("title", "")
        industry = extractor_data.get("industry") or context.get("industry", "SaaS")
        solution = extractor_data.get("proposed_solution", "")
        problem = extractor_data.get("problem_statement", "")

        # Search for actual market competitors
        search_query = f"top competitors alternatives companies offering {solution} {industry}"
        search_results = self.search_service.search(search_query, max_results=5)
        web_context_str = "\n".join([f"- [{s.get('title')}]: {s.get('snippet')} ({s.get('url')})" for s in search_results])

        system_prompt = (
            "You are a Senior Competitive Intelligence Strategist. "
            "Analyze the competitor landscape, identifying both direct and indirect competitors, their business models, "
            "pricing tiers, customer gripes/weaknesses, and the founder's unfair advantage. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Evaluate competitors for this startup:
Title: {title}
Industry: {industry}
Product Solution: {solution}
Problem Solved: {problem}

Live Web Research Data:
{web_context_str}

Return a valid JSON object with the following exact keys:
{{
  "competitors": [
    {{
      "name": "Competitor Name",
      "competitor_type": "Direct" or "Indirect" or "Legacy Alternative",
      "website_url": "https://example.com",
      "pricing_model": "e.g. $49/mo per user or Custom Enterprise quote",
      "features": "2-3 primary features (e.g. Workflow builder, automated exports, API connectors)",
      "strengths": "1-2 primary strengths",
      "weaknesses": "1-2 documented customer complaints or limitations",
      "market_gap": "What they miss that this startup can capitalize on",
      "source_reference": "Name of source / URL",
      "verified_source": true
    }}
  ],
  "competitive_advantages": [
    "Unfair advantage 1",
    "Unfair advantage 2"
  ],
  "defensibility_score": 78,
  "market_saturation": "Low" or "Moderate" or "High",
  "positioning_recommendation": "Strategic guidance on how to position against these players",
  "sources": {json.dumps(search_results)}
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.groq_service.chat_completion(messages, temperature=0.3, json_mode=True)

    def _execute_fallback(self, context):
        extractor_data = context.get("extractor_data", {})
        title = context.get("title", "Startup")
        industry = extractor_data.get("industry") or context.get("industry", "Technology")
        solution = extractor_data.get("proposed_solution", "")
        
        search_results = self.search_service.search_competitors(industry, title)

        # Context-dependent fallback competitors
        lower = f"{title} {solution} {industry}".lower()
        if "contract" in lower or "legal" in lower:
            comp_list = [
                {
                    "name": "Ironclad / ContractPodAi",
                    "competitor_type": "Legacy Enterprise",
                    "website_url": "https://ironcladapp.com",
                    "pricing_model": "Custom Enterprise ($15,000+/yr)",
                    "features": "Enterprise CLM, workflow approvals, Salesforce integration, SOC2 audit trails",
                    "strengths": "Deep enterprise workflows, robust audit compliance, strong security certifications.",
                    "weaknesses": "Prohibitively expensive for SMBs/freelancers, months-long implementation cycle.",
                    "market_gap": "Instant self-serve contract reviews priced for independent operators.",
                    "source_reference": "G2 Enterprise Grid",
                    "verified_source": False
                },
                {
                    "name": "Robin AI",
                    "competitor_type": "Direct AI Competitor",
                    "website_url": "https://robinai.com",
                    "pricing_model": "Mid-Market SaaS ($150-$500/mo)",
                    "features": "Legal LLM contract review, in-house legal team review, clause redlining",
                    "strengths": "Advanced legal LLM tuning and in-house legal team review.",
                    "weaknesses": "Geared towards in-house corporate legal counsels, not individual creators.",
                    "market_gap": "Plain-English risk translations with freelancer-specific rate and indemnification protection.",
                    "source_reference": "LegalTech Landscape Report",
                    "verified_source": False
                },
                {
                    "name": "Generic LLMs (ChatGPT / Claude)",
                    "competitor_type": "Indirect Alternative",
                    "website_url": "https://openai.com",
                    "pricing_model": "$20/mo general subscription",
                    "features": "General prompt chat, freeform text editing, multi-language translation",
                    "strengths": "Cheap, widely accessible, general text parsing.",
                    "weaknesses": "Lacks domain-specific liability heuristics, formatting retention, and persistent clause databases.",
                    "market_gap": "Dedicated domain workflow, auto-redlining, and client pushback email generator.",
                    "source_reference": "User Survey Analytics",
                    "verified_source": False
                }
            ]
        elif "carbon" in lower or "climate" in lower or "esg" in lower:
            comp_list = [
                {
                    "name": "Watershed Climate",
                    "competitor_type": "Direct Enterprise",
                    "website_url": "https://watershed.com",
                    "pricing_model": "Enterprise SaaS ($25k-$100k/yr)",
                    "features": "Scope 1-3 ledger, emissions factor databases, consulting audit onboarding",
                    "strengths": "Backed by top tier VCs, massive emissions factor database.",
                    "weaknesses": "High price floor, requires heavy consulting and manual data onboarding.",
                    "market_gap": "Lightweight plug-and-play carbon tracking for mid-market suppliers.",
                    "source_reference": "ClimateTech Market Map",
                    "verified_source": False
                },
                {
                    "name": "Persefoni",
                    "competitor_type": "Direct",
                    "website_url": "https://persefoni.com",
                    "pricing_model": "Enterprise Tiered",
                    "features": "CSRD/SEC compliance dashboards, financial institution accounting, ERP connectors",
                    "strengths": "Strict SEC/CSRD regulatory alignment, financial institution depth.",
                    "weaknesses": "Complex UI requiring trained sustainability consultants.",
                    "market_gap": "Automated invoice parsing and real-time Scope 3 supply chain supplier portals.",
                    "source_reference": "GreenBiz Tech Review",
                    "verified_source": False
                }
            ]
        else:
            comp_list = [
                {
                    "name": "Incumbent Market Leader A",
                    "competitor_type": "Direct",
                    "website_url": "https://example-leader.com",
                    "pricing_model": "$79/user/month (Annual contract required)",
                    "features": "Comprehensive legacy workflows, user permission hierarchies, custom reports",
                    "strengths": "Extensive brand reputation, established distribution channels, deep integrations.",
                    "weaknesses": "Cluttered legacy user experience, slow product iteration, rigid contract locks.",
                    "market_gap": "Modern streamlined UI, transparent monthly pricing, and AI-native automation.",
                    "source_reference": "G2 Category Leaderboard",
                    "verified_source": False
                },
                {
                    "name": "Niche Specialist B",
                    "competitor_type": "Indirect",
                    "website_url": "https://example-niche.com",
                    "pricing_model": "Freemium ($29/mo starter)",
                    "features": "Lightweight REST API, webhooks, community templates, basic dashboard",
                    "strengths": "Strong developer community, lightweight API.",
                    "weaknesses": "Lacks comprehensive end-to-end features, limited customer support.",
                    "market_gap": "Complete turnkey experience requiring zero code or configuration.",
                    "source_reference": "Product Hunt Trending",
                    "verified_source": False
                },
                {
                    "name": "Manual In-House Workarounds (Spreadsheets & Email)",
                    "competitor_type": "Status Quo Alternative",
                    "website_url": "https://workspace.google.com",
                    "pricing_model": "$6 - $18/mo",
                    "features": "Manual cell calculations, custom formula rows, local file exports",
                    "strengths": "Familiarity, zero additional software spend.",
                    "weaknesses": "High human error rates, zero automation, impossible to scale.",
                    "market_gap": "Replaces 20 hours of manual spreadsheet reconciliation with instant automated insights.",
                    "source_reference": "Industry Workflow Benchmarks",
                    "verified_source": False
                }
            ]

        return {
            "competitors": comp_list,
            "competitive_advantages": [
                "AI-native workflow reducing task completion time by up to 80%",
                "Self-serve onboarding with immediate time-to-value within 5 minutes",
                "Transparent, predictable pricing model without forced enterprise sales calls"
            ],
            "defensibility_score": 76,
            "market_saturation": "Moderate",
            "positioning_recommendation": f"Position '{title}' as the agile, intelligent alternative that eliminates the bloat and complexity of incumbent software.",
            "sources": search_results
        }
