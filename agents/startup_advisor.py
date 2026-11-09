import json
from .base_agent import BaseAgent

class StartupAdvisorAgent(BaseAgent):
    """Agent 7: Conversational AI advisor answering strategic questions rooted in the idea's validation data"""

    def __init__(self):
        super().__init__(
            name="advisor",
            description="Conversational startup mentor that provides tailored strategic advice based on complete validation analysis."
        )

    def answer_query(self, user_query, idea_dict, analysis_dict, conversation_history=None):
        """
        Answers founder questions with full context awareness.
        """
        conversation_history = conversation_history or []

        # Build context brief
        title = idea_dict.get("title", "Startup Idea")
        industry = idea_dict.get("industry", "Technology")
        score = idea_dict.get("viability_score", 78)
        rec = idea_dict.get("recommendation", "Strong Pursue")

        extractor_data = analysis_dict.get("extractor", {}).get("data", {})
        market_data = analysis_dict.get("market", {}).get("data", {})
        competitor_data = analysis_dict.get("competitors", {}).get("data", {})
        swot_data = analysis_dict.get("swot_risk", {}).get("data", {})
        mvp_data = analysis_dict.get("mvp", {}).get("data", {})
        gtm_data = analysis_dict.get("gtm", {}).get("data", {})

        system_prompt = f"""
You are the AI Startup Advisor, an elite Silicon Valley venture architect, serial founder, and startup mentor.
You have the complete analysis and validation data for the founder's startup:

Startup Name: {title}
Industry: {industry}
Viability Score: {score}/100 ({rec})
Business Concept: {extractor_data.get('business_concept', '')}
Core Problem: {extractor_data.get('problem_statement', '')}
Proposed Solution: {extractor_data.get('proposed_solution', '')}
Target Audience: {extractor_data.get('target_audience', '')}
Revenue Model: {extractor_data.get('revenue_model', '')}
TAM / SAM / SOM: {market_data.get('tam', '')} / {market_data.get('sam', '')} / {market_data.get('som', '')}
Competitor Gap: {competitor_data.get('positioning_recommendation', '')}
Identified Key Risks: {json.dumps([r.get('risk') for r in swot_data.get('risks', [])[:3]])}
Essential MVP Features: {json.dumps(mvp_data.get('must_have', [])[:3])}
GTM Pricing: {json.dumps(gtm_data.get('pricing_strategy', {}).get('tiers', [])[:2])}

Guidelines:
- Give crisp, actionable, founder-friendly advice with numbered or bulleted takeaways.
- Refer directly to the startup's actual numbers, competitor landscape, and validation data when relevant.
- Be encouraging yet realistic, pointing out potential blind spots and tactical next steps.
- Keep responses direct, high-value, and focused (approx 150-300 words).
"""

        messages = [{"role": "system", "content": system_prompt}]

        # Append last 6 turns of history for continuity
        for msg in conversation_history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("message", "")})

        messages.append({"role": "user", "content": user_query})

        if self.groq_service.is_available():
            try:
                response = self.groq_service.chat_completion(messages, temperature=0.6, max_tokens=700)
                return {
                    "reply": response,
                    "source": "Groq LLM Inference (Live)",
                    "status": "success"
                }
            except Exception as e:
                # Fallback to analytical advisor reply
                pass

        # Intelligent Fallback Advisor Engine
        return {
            "reply": self._generate_fallback_advisor_reply(user_query, idea_dict, analysis_dict),
            "source": "AI Startup Advisor (Simulated Analytical Mode)",
            "status": "success"
        }

    def _execute_llm(self, context):
        title = context.get("title", "Startup Idea")
        industry = context.get("industry", "Technology")
        extractor_data = context.get("extractor_data", {})
        market_data = context.get("market_data", {})
        competitor_data = context.get("competitor_data", {})
        swot_data = context.get("swot_data", {})
        mvp_data = context.get("mvp_data", {})
        gtm_data = context.get("gtm_data", {})

        system_prompt = (
            "You are a Silicon Valley Startup Advisor, Serial Tech Founder, and Venture Partner. "
            "Synthesize all previous agent intelligence to generate an actionable strategic advisory brief for the founder. "
            "Return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""
Provide strategic founder advisory guidance for:
Startup: {title}
Industry: {industry}
Business Concept: {extractor_data.get('business_concept', '')}
TAM/SAM/SOM: {market_data.get('tam', '')} / {market_data.get('sam', '')} / {market_data.get('som', '')}
Competitor Wedge: {competitor_data.get('positioning_recommendation', '')}
Must-Have MVP Scope: {json.dumps(mvp_data.get('must_have', [])[:3])}

Return a valid JSON object with the following exact keys:
{{
  "advisory_summary": "Crisp 2-sentence executive guidance for the founder",
  "top_strategic_recommendations": [
    "High-priority recommendation 1",
    "High-priority recommendation 2",
    "High-priority recommendation 3"
  ],
  "first_100_customers_playbook": "Concrete non-scalable customer acquisition strategy for initial 100 users",
  "pricing_and_unit_economics_advice": "Actionable guidance on trial structure and pricing tier anchor",
  "fundraising_readiness": "Assessment of whether to bootstrap vs raise angel/pre-seed capital",
  "key_red_flags_to_monitor": ["Red flag 1 to watch", "Red flag 2 to watch"],
  "founder_elevator_pitch": "Compelling 60-second elevator pitch script"
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.groq_service.chat_completion(messages, temperature=0.4, json_mode=True)

    def _execute_fallback(self, context):
        title = context.get("title", "Startup Platform")
        industry = context.get("industry", "B2B SaaS")
        extractor_data = context.get("extractor_data", {})
        target_audience = extractor_data.get("target_audience", "prospective customers")
        solution = extractor_data.get("proposed_solution", "an automated workflow")

        return {
            "advisory_summary": f"Focus ruthlessly on closing your first 20 reference customers in {industry} through non-scalable direct founder outreach before spending money on digital ads.",
            "top_strategic_recommendations": [
                f"Validate problem urgency with 15 customer discovery interviews targeting {target_audience}.",
                "Keep MVP scope strictly constrained to the core automated value loop and resist feature creep.",
                "Implement a 14-day reverse trial rather than a permanent free plan to protect compute margins."
            ],
            "first_100_customers_playbook": "Deploy personalized Loom video audits to 100 vetted LinkedIn leads, partner with complementary SaaS tools, and execute a high-signal Product Hunt launch.",
            "pricing_and_unit_economics_advice": "Anchor on a $79/mo Pro plan as the primary revenue driver, backed by a $29/mo starter tier for low-friction self-serve adoption.",
            "fundraising_readiness": "Bootstrap through initial MVP validation and 25 paying pilot customers. Reach $5k-$10k MRR to command higher valuations in angel/pre-seed rounds.",
            "key_red_flags_to_monitor": [
                "Day-30 retention below 50% indicating onboarding friction or low workflow stickiness.",
                "Customer Acquisition Cost (CAC) exceeding 1/3 of first-year Customer Lifetime Value (LTV)."
            ],
            "founder_elevator_pitch": f"We are building {title}, an intelligent platform that enables {target_audience} to automate their most painful workflows, delivering 10x faster execution without the cost of legacy enterprise software."
        }

    def _generate_fallback_advisor_reply(self, query, idea, analyses):
        q = query.lower()
        title = idea.get("title", "your startup")
        industry = idea.get("industry", "your sector")

        if "customer" in q or "acquire" in q or "first 100" in q:
            return f"""### 🎯 How to Acquire Your First 100 Paying Customers for {title}

Getting your initial customer base requires non-scalable, high-touch outreach rather than paid advertising:

1. **Targeted Direct Founder Outbound (First 20 Customers):**
   - Identify 100 ideal prospects on LinkedIn matching your ICP.
   - Send personalized Loom video audits showing how manual inefficiencies currently cost them time.
   - Offer an exclusive 'Founding Member' lifetime discount in exchange for bi-weekly feedback interviews.

2. **Community & Content Seeding (Customers 21-50):**
   - Write comprehensive case studies or teardowns in relevant industry forums and subreddits.
   - Share transparent 'building in public' metric milestones on LinkedIn/X to build trust.

3. **High-Impact Product Hunt Launch (Customers 51-100):**
   - Coordinate your launch date with 25+ supportive beta testers for upvote velocity.
   - Offer an irresistible launch-day incentive (e.g., free onboarding + 2 months free on the Pro tier).

**Key Metric to Track:** Focus on *Day-30 Retention* over gross signups. If early customers don't log in at least 3x/week, iterate on the onboarding experience before scaling marketing spend."""

        elif "pricing" in q or "monetiz" in q or "charge" in q:
            return f"""### 💡 Recommended Pricing Architecture for {title}

Based on your market validation data in {industry}:

1. **Self-Serve Starter Tier ($29/month):**
   - Low enough barrier for individual practitioners to swipe a personal corporate card without managerial procurement approvals.
   - Includes core automated workflows and standard exports.

2. **Growth / Pro Tier ($79 - $99/month - Anchor Tier):**
   - The primary revenue driver. Introduce team collaboration seats and unlimited processing.
   - Highlight this tier as **'Most Popular'** on your pricing page.

3. **Enterprise / Agency Custom ($249+/month):**
   - Includes custom API webhooks, compliance/audit data exports, and dedicated Slack channel support.

**Crucial Pricing Rule:** Do not offer an unlimited free tier. Use a **14-day reverse trial** (users start on Pro for 14 days without a credit card, then choose a paid tier). This protects your API compute margins while establishing value upfront."""

        elif "competitor" in q or "defend" in q or "moat" in q:
            return f"""### 🛡️ Building a Defensible Moat Against Competitors

In {industry}, large incumbents move slowly and carry heavy technical debt:

1. **Velocity of User Experience:**
   - Your primary wedge is **time-to-value**. An incumbent requires 3 enterprise sales demo calls and a 6-week onboarding process. You must deliver value within **3 minutes of signup**.

2. **Proprietary Workflow & Telemetry:**
   - As users execute workflows on {title}, gather structured preference data. Use this proprietary context to fine-tune automated suggestions that become more accurate with every use.

3. **Vertical Specialization:**
   - Generic platforms (like general AI tools) attempt to solve everything for everyone. Win by being the deepest, most intuitive solution tailored specifically for your target ICP."""

        else:
            return f"""### 🚀 Strategic Guidance for {title}

Thank you for your question regarding **{title}** in the **{industry}** domain.

Here are the 3 top priorities your startup should execute over the next 14 days:

1. **Validate Problem Urgency with 10 Customer Discovery Interviews:**
   - Before writing complex code, ask prospective users: *"How do you currently handle this problem, and how much money or hours did that cost you last month?"*
   - If they aren't actively spending money or time trying to solve it today, narrow your value proposition.

2. **Tighten the MVP Scope to 1 Core Loop:**
   - Resist feature creep. Launch with your top **Must-Have** feature and deliver an exceptional, bug-free experience.

3. **Establish a Transparent Metrics Baseline:**
   - Track your Customer Acquisition Cost (CAC) and Activation Rate from Day 1.

Would you like me to help you draft your cold outreach script, design an investor pitch outline, or map out your landing page copy?"""
