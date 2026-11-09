import json
from .base_agent import BaseAgent

class IdeaExtractionAgent(BaseAgent):
    """Agent 1: Extracts structured startup information from free-form natural language text"""

    def __init__(self):
        super().__init__(
            name="extractor",
            description="Extracts structured business concept, problem, solution, target audience, industry, and revenue model."
        )

    def _execute_llm(self, context):
        raw_idea = context.get("raw_description", "")
        title_hint = context.get("title", "")
        industry_hint = context.get("industry", "")

        system_prompt = (
            "You are a Senior Startup Incubator Director and Venture Architect. "
            "Analyze the founder's raw startup idea and extract structured business intelligence. "
            "You must return ONLY a valid JSON object matching the requested schema with no commentary or markdown ticks."
        )

        user_prompt = f"""
Analyze this startup submission:
Title: {title_hint}
Industry: {industry_hint}
Raw Idea Description:
{raw_idea}

Return a valid JSON object with the following exact keys:
{{
  "business_concept": "concise 2-sentence executive summary of the business concept",
  "problem_statement": "clear articulation of the pain point or inefficiency in the market",
  "proposed_solution": "detailed description of how the product/service solves this pain point",
  "target_audience": "primary user personas and target buyers (B2B/B2C)",
  "industry": "the primary industry sector (e.g. B2B SaaS, FinTech, HealthTech, AI, EdTech, E-Commerce, DevTools)",
  "revenue_model": "monetization model (e.g. Monthly SaaS Subscription, Usage-Based, Marketplace Take-Rate, Freemium)",
  "unique_value_proposition": "the single compelling reason customers will switch to this solution",
  "suggested_tags": ["tag1", "tag2", "tag3"]
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.groq_service.chat_completion(messages, temperature=0.3, json_mode=True)

    def _execute_fallback(self, context):
        raw_idea = context.get("raw_description", "")
        title = context.get("title", "Untitled Startup")
        industry = context.get("industry") or "B2B SaaS / Technology"

        # Domain heuristic detection
        lower = raw_idea.lower()
        if "freelance" in lower or "contract" in lower or "legal" in lower:
            extracted_industry = "LegalTech / Productivity SaaS"
            revenue_model = "Tiered Monthly Subscription ($19-$49/mo)"
            target_audience = "Freelance developers, independent designers, boutique agencies, and solopreneurs"
            problem = "Freelancers frequently sign disadvantageous contracts or spend thousands on lawyers for simple agreement reviews."
            solution = "An AI-powered contract analysis tool that flags indemnification clauses, payment terms, and scope creep risks in plain English."
            uvp = "Instant redline warnings and contract scoring tailored specifically for independent creators."
        elif "carbon" in lower or "climate" in lower or "sustain" in lower:
            extracted_industry = "ClimateTech / Enterprise ESG"
            revenue_model = "Annual Enterprise License ($12k-$60k/yr)"
            target_audience = "Mid-market manufacturing, logistics companies, and corporate sustainability officers"
            problem = "Companies struggle to aggregate and audit Scope 1, 2, and 3 carbon emissions for mandatory ESG compliance."
            solution = "Automated carbon accounting platform integrating ERP data, utility bills, and supply chain telemetry into certified ESG audits."
            uvp = "Automated invoice-to-carbon telemetry reducing audit prep time from 4 months to 2 days."
        elif "health" in lower or "medical" in lower or "patient" in lower:
            extracted_industry = "Digital Health / MedTech"
            revenue_model = "Per-Provider Subscription + HIPAA Enterprise Tiers"
            target_audience = "Private clinics, outpatient physicians, and wellness practices"
            problem = "Doctors waste 15+ hours weekly on clinical documentation and billing compliance."
            solution = "Ambient AI clinical scribe and automated billing coder that converts patient consultations into compliant EHR notes."
            uvp = "Zero-click clinical note generation with real-time ICD-10 reimbursement accuracy."
        else:
            extracted_industry = industry
            revenue_model = "Tiered Subscription (B2B SaaS / Freemium)"
            target_audience = "Digital teams, business professionals, and growing SMEs"
            problem = f"Existing market solutions addressing '{title}' are disjointed, expensive, or require high manual overhead."
            solution = f"A modern cloud platform that automates workflows for '{title}', delivering 10x faster execution."
            uvp = "End-to-end automation with seamless integrations, intuitive onboarding, and measurable time savings."

        return {
            "business_concept": f"{title} is an automated platform targeting {target_audience} in {extracted_industry}.",
            "problem_statement": problem,
            "proposed_solution": solution,
            "target_audience": target_audience,
            "industry": extracted_industry,
            "revenue_model": revenue_model,
            "unique_value_proposition": uvp,
            "suggested_tags": [extracted_industry.split()[0], "Automation", "AI-Powered", "Cloud"]
        }
