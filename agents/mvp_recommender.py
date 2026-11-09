import json
from .base_agent import BaseAgent

class MVPRecommenderAgent(BaseAgent):
    """Agent 5: Formulates MoSCoW MVP feature scoping and Effort vs Impact prioritization"""

    def __init__(self):
        super().__init__(
            name="mvp",
            description="Recommends core MVP feature set, separates must-haves from future scope, and builds effort vs impact matrix."
        )

    def _execute_llm(self, context):
        extractor_data = context.get("extractor_data", {})
        market_data = context.get("market_data", {})
        title = context.get("title", "")
        solution = extractor_data.get("proposed_solution", "")
        problem = extractor_data.get("problem_statement", "")

        system_prompt = (
            "You are a Chief Product Officer (CPO) and Agile Startup Architect. "
            "Formulate an ultra-lean, high-impact MVP scope that enables the founder to launch within 6-8 weeks. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Plan MVP features for:
Startup: {title}
Core Problem: {problem}
Proposed Solution: {solution}
Target Audience: {extractor_data.get('target_audience', '')}

Return a valid JSON object with the following exact keys:
{{
  "must_have": [
    "Core feature 1 (vital for core value loop)",
    "Core feature 2",
    "Core feature 3"
  ],
  "should_have": [
    "Important feature 1 (phase 2 enhancement)",
    "Important feature 2"
  ],
  "could_have": [
    "Nice-to-have feature 1",
    "Nice-to-have feature 2"
  ],
  "wont_have": [
    "Out of scope feature 1 (distraction for v1)",
    "Out of scope feature 2"
  ],
  "effort_vs_impact": [
    {{"feature": "Feature Name", "impact": "High", "effort": "Low", "quadrant": "Quick Win"}},
    {{"feature": "Feature Name", "impact": "High", "effort": "High", "quadrant": "Major Project"}},
    {{"feature": "Feature Name", "impact": "Low", "effort": "Low", "quadrant": "Fill-In"}},
    {{"feature": "Feature Name", "impact": "Low", "effort": "High", "quadrant": "Thankless Task"}}
  ],
  "estimated_mvp_weeks": 6,
  "weekly_milestones": [
    {{"week": "Week 1", "phase": "Architecture & Data Scaffold", "focus": "Setup DB models, API auth, and core UI shell", "deliverables": ["DB schema initialized", "User auth working", "UI layout ready"]}},
    {{"week": "Week 2", "phase": "Core Processing Engine", "focus": "Build the primary value-delivering workflow loop", "deliverables": ["Input parser working", "AI prompt pipeline connected", "Result serialization"]}},
    {{"week": "Week 3", "phase": "Dashboard & Visualizations", "focus": "Develop responsive charts, result cards, and metrics", "deliverables": ["Interactive Chart.js visualizer", "Detail drill-downs", "Responsive mobile UI"]}},
    {{"week": "Week 4", "phase": "Billing & Export Engines", "focus": "Implement Stripe subscriptions, PDF generator, and CSV exports", "deliverables": ["Stripe tiered billing", "PDF export engine", "CSV data downloads"]}},
    {{"week": "Week 5", "phase": "Closed Beta & Feedback", "focus": "Onboard 15 initial ICP pilot users and iterate on feedback", "deliverables": ["Closed waitlist invites", "In-app telemetry", "User feedback sprints"]}},
    {{"week": "Week 6", "phase": "Public Launch & Distribution", "focus": "Public launch on Product Hunt and community channels", "deliverables": ["Product Hunt launch sequence", "100 ICP outreach emails", "First paying conversions"]}}
  ],
  "recommended_tech_stack": [
    {{"layer": "Frontend", "tech": "React / Next.js or Tailwind HTML"}},
    {{"layer": "Backend", "tech": "Python / Flask or FastAPI"}},
    {{"layer": "Database", "tech": "PostgreSQL / Supabase"}},
    {{"layer": "AI / Processing", "tech": "Groq / OpenAI API"}}
  ],
  "first_milestone_metric": "e.g. 50 active users completing core workflow with 60%+ retention"
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
        solution = extractor_data.get("proposed_solution", "automated software platform")

        return {
            "must_have": [
                "Self-serve frictionless user authentication and workspace onboarding",
                "Core automated processing engine delivering the primary promise within 60 seconds",
                "Actionable result summary dashboard with 1-click export (PDF / CSV / Shareable link)",
                "Basic feedback loop and customer usage telemetry"
            ],
            "should_have": [
                "Stripe billing integration with automated tiered subscriptions & trials",
                "Team collaboration invites and role-based workspace permissions",
                "Automated email notifications and weekly activity digests"
            ],
            "could_have": [
                "Custom webhooks and Zapier / Make automation connectors",
                "Dark/light mode aesthetic customization",
                "Advanced multi-language localization"
            ],
            "wont_have": [
                "Custom enterprise on-premise deployments (defers focus)",
                "Complex multi-tiered approval hierarchy workflows",
                "Native mobile apps before web PMF validation"
            ],
            "effort_vs_impact": [
                {
                    "feature": "1-Click Core Automated Pipeline",
                    "impact": "High",
                    "effort": "Medium",
                    "quadrant": "Quick Win"
                },
                {
                    "feature": "Instant PDF / Executive Export Engine",
                    "impact": "High",
                    "effort": "Low",
                    "quadrant": "Quick Win"
                },
                {
                    "feature": "Proprietary Fine-Tuned Domain AI Model",
                    "impact": "High",
                    "effort": "High",
                    "quadrant": "Major Project"
                },
                {
                    "feature": "Custom Theme & Palette Switcher",
                    "impact": "Low",
                    "effort": "Low",
                    "quadrant": "Fill-In"
                },
                {
                    "feature": "Custom SSO / SAML Enterprise Auth for Day 1",
                    "impact": "Low",
                    "effort": "High",
                    "quadrant": "Thankless Task"
                }
            ],
            "estimated_mvp_weeks": 6,
            "weekly_milestones": [
                {
                    "week": "Week 1",
                    "phase": "Architecture & Core Schema",
                    "focus": "Setup database models, REST routing, authentication, and responsive layout.",
                    "deliverables": ["SQLite schema initialized", "User registration & session management", "Dashboard wireframe ready"],
                    "status": "completed",
                    "progress_pct": 100
                },
                {
                    "week": "Week 2",
                    "phase": "Core Processing Pipeline",
                    "focus": f"Build the automated workflow engine for {title} with prompt templates.",
                    "deliverables": ["Input parameter extraction working", "AI prompt orchestration connected", "Result JSON serialization"],
                    "status": "in_progress",
                    "progress_pct": 75
                },
                {
                    "week": "Week 3",
                    "phase": "Interactive Dashboard & Visualizations",
                    "focus": "Implement Chart.js radar & doughnut charts, detail cards, and responsiveness.",
                    "deliverables": ["Interactive viability radar chart", "MoSCoW roadmap cards", "Mobile/tablet layout optimization"],
                    "status": "pending",
                    "progress_pct": 40
                },
                {
                    "week": "Week 4",
                    "phase": "Subscriptions & Multi-Format Exports",
                    "focus": "Integrate Stripe checkout, ReportLab PDF generation, and CSV downloads.",
                    "deliverables": ["Stripe checkout & tier webhooks", "ReportLab PDF vector report builder", "CSV & Markdown export endpoints"],
                    "status": "pending",
                    "progress_pct": 20
                },
                {
                    "week": "Week 5",
                    "phase": "Closed Beta & Feedback Sprints",
                    "focus": "Onboard 15 initial ICP pilot users and run weekly feedback iterations.",
                    "deliverables": ["Closed alpha waitlist invites", "In-app telemetry & error tracking", "Usability feedback backlog"],
                    "status": "pending",
                    "progress_pct": 0
                },
                {
                    "week": "Week 6",
                    "phase": "Public Launch & Distribution Wedge",
                    "focus": "Execute Product Hunt launch sequence, targeted cold email, and paid conversions.",
                    "deliverables": ["Product Hunt & Hacker News launch", "100 personalized ICP outreach emails", "Target first 25 paying subscribers"],
                    "status": "pending",
                    "progress_pct": 0
                }
            ],
            "recommended_tech_stack": [
                {"layer": "Frontend UI", "tech": "Bootstrap 5 + Modern JavaScript & Chart.js"},
                {"layer": "Application Backend", "tech": "Python / Flask REST Microservices"},
                {"layer": "Database & State", "tech": "SQLite (dev) / PostgreSQL (production)"},
                {"layer": "AI Inference Engine", "tech": "Groq Llama 3.3 Versatile API"}
            ],
            "first_milestone_metric": "30 paying beta customers who use the platform at least 3x per week"
        }
