import json
from .base_agent import BaseAgent

class GTMStrategistAgent(BaseAgent):
    """Agent 6: Formulates positioning, pricing tiers, customer acquisition channels, and 90-day launch roadmap"""

    def __init__(self):
        super().__init__(
            name="gtm",
            description="Designs marketing positioning, pricing model, customer acquisition funnels, and 90-day launch milestones."
        )

    def _execute_llm(self, context):
        extractor_data = context.get("extractor_data", {})
        market_data = context.get("market_data", {})
        title = context.get("title", "")
        industry = extractor_data.get("industry", "SaaS")

        system_prompt = (
            "You are a Chief Marketing Officer (CMO) and Venture Growth Strategist. "
            "Formulate an aggressive, capital-efficient Go-to-Market (GTM) strategy with realistic customer acquisition channels, "
            "pricing psychology, and a 90-day launch roadmap. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Build GTM strategy for:
Startup: {title}
Industry: {industry}
Target Audience: {extractor_data.get('target_audience', '')}
UVP: {extractor_data.get('unique_value_proposition', '')}
Current Competitor Gap: {context.get('competitor_data', {}).get('positioning_recommendation', '')}

Return a valid JSON object with the following exact keys:
{{
  "positioning_statement": "For [target audience] who [problem], [startup name] is a [category] that [key benefit]. Unlike [competitor alternatives], [startup name] [primary differentiator].",
  "ideal_customer_profile": {{
    "company_type": "e.g. Mid-market agencies or Individual creators",
    "team_size": "1-50 employees",
    "key_trigger_event": "Why they are buying right now",
    "primary_decision_maker": "Job title"
  }},
  "acquisition_channels": [
    "Channel 1 (e.g. Targeted Cold Email to niche VPs with 4% reply rate)",
    "Channel 2 (e.g. SEO Content targeting high-intent long-tail keywords)",
    "Channel 3 (e.g. Product Hunt launch & Indie Hackers community distribution)"
  ],
  "pricing_strategy": {{
    "model_name": "Tiered SaaS Subscription",
    "rationale": "Why this model fits user psychology",
    "tiers": [
      {{"name": "Starter", "price": "$29/mo", "target": "Solopreneurs / Freelancers", "features": "Core feature set"}},
      {{"name": "Growth / Pro", "price": "$79/mo", "target": "Growing teams", "features": "Unlimited automation & priority processing"}},
      {{"name": "Business / Enterprise", "price": "$249/mo+", "target": "Agencies & Companies", "features": "Dedicated SLA, API access, team seats"}}
    ]
  }},
  "launch_roadmap_90_days": [
    {{"phase": "Days 1-30: Pre-Launch Validation", "milestones": ["Build landing page waitlist", "Interview 30 prospective users", "Ship Alpha to 15 design partners"]}},
    {{"phase": "Days 31-60: Beta & Product-Market Fit", "milestones": ["Launch closed private beta", "Implement feedback sprints", "Achieve 40%+ Day-7 retention"]}},
    {{"phase": "Days 61-90: Public Launch & Scaling", "milestones": ["Execute Product Hunt / Hacker News launch", "Turn on self-serve Stripe billing", "Target first $3,000 MRR"]}}
  ],
  "first_year_target_arr": "$100,000 ARR"
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
        industry = extractor_data.get("industry", "SaaS")
        audience = extractor_data.get("target_audience", "Independent operators and business teams")
        uvp = extractor_data.get("unique_value_proposition", "Automated intelligence with zero friction")

        return {
            "positioning_statement": f"For {audience} struggling with manual inefficiencies, {title} is an intelligent {industry} copilot that delivers {uvp}. Unlike legacy enterprise suites, {title} offers immediate self-serve setup and measurable ROI within minutes.",
            "ideal_customer_profile": {
                "company_type": "Bootstrapped startups, agile SMBs, and digital operators",
                "team_size": "2 to 45 team members",
                "key_trigger_event": "Hitting an operational ceiling where manual tasks bottleneck revenue growth",
                "primary_decision_maker": "Founder, Head of Operations, or Lead Practitioner"
            },
            "acquisition_channels": [
                "Organic Content & Programmatic SEO targeting high-intent 'alternative to [competitor]' search queries",
                "High-signal Community Engagement on LinkedIn, X/Twitter, and niche Reddit communities",
                "Co-marketing partnerships with complementary non-competing SaaS platforms",
                "High-impact launch sequence on Product Hunt, Hacker News, and BetaList"
            ],
            "pricing_strategy": {
                "model_name": "Value-Metric Tiered SaaS Subscription",
                "rationale": "Aligns pricing with volume of work processed, making the starter tier frictionless while enabling account expansion.",
                "tiers": [
                    {
                        "name": "Starter",
                        "price": "$29/month",
                        "target": "Individual practitioners & solo operators",
                        "features": "Up to 50 automated operations/mo, standard email support, core exports"
                    },
                    {
                        "name": "Professional",
                        "price": "$79/month",
                        "target": "Fast-moving boutique teams (Most Popular)",
                        "features": "Unlimited processing, team collaboration (3 seats), advanced integrations"
                    },
                    {
                        "name": "Scale / Organization",
                        "price": "$249/month",
                        "target": "Established agencies & mid-market companies",
                        "features": "Dedicated account manager, custom webhooks, enterprise SLA, 10 team seats"
                    }
                ]
            },
            "launch_roadmap_90_days": [
                {
                    "phase": "Days 1-30: Closed Alpha & Validation",
                    "milestones": [
                        "Deploy high-converting landing page with interactive product demo video",
                        "Recruit 20 vetted beta users from target online communities",
                        "Conduct weekly feedback calls and tighten onboarding funnel"
                    ]
                },
                {
                    "phase": "Days 31-60: Beta & Retention Engine",
                    "milestones": [
                        "Launch closed public beta with waitlist invite codes",
                        "Activate automated Stripe billing checkout flow",
                        "Verify that 70%+ of beta cohorts return weekly"
                    ]
                },
                {
                    "phase": "Days 61-90: Scale & Revenue Acceleration",
                    "milestones": [
                        "Execute top-ranked Product Hunt launch campaign",
                        "Launch partner affiliate program offering 25% recurring commissions",
                        "Reach milestone of 50 paying customers ($2,500+ MRR)"
                    ]
                }
            ],
            "first_year_target_arr": "$120,000 ARR"
        }
