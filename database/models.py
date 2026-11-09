import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .db import get_db

def normalize_recommendation(rec, score=0):
    """Normalizes any recommendation text to PROCEED, IMPROVE, or RECONSIDER"""
    if not rec or rec == 'Pending Validation' or rec == 'Pending':
        if score >= 75:
            return "PROCEED"
        elif score >= 55:
            return "IMPROVE"
        elif score > 0:
            return "RECONSIDER"
        return "PENDING"
    r = str(rec).upper()
    if "PROCEED" in r or "PURSUE" in r or "STRONG" in r:
        return "PROCEED"
    elif "IMPROVE" in r or "POTENTIAL" in r or "MODERATE" in r:
        return "IMPROVE"
    elif "RECONSIDER" in r or "PIVOT" in r or "RISK" in r or "HALT" in r:
        return "RECONSIDER"
    return "IMPROVE" if score >= 55 else "RECONSIDER"


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, full_name, created_at, role='entrepreneur'):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.created_at = created_at
        self.role = role

    @classmethod
    def get_by_id(cls, user_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_by_email(cls, email):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            row = cursor.fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def get_by_username(cls, username):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
            row = cursor.fetchone()
            if row:
                return cls(**dict(row))
        return None

    @classmethod
    def create(cls, username, email, password, full_name=None):
        hashed = generate_password_hash(password)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            """, (username.strip(), email.strip(), hashed, full_name or username))
            user_id = cursor.lastrowid
        return cls.get_by_id(user_id)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": str(self.created_at),
            "role": self.role
        }


class StartupIdea:
    @classmethod
    def create(cls, user_id, title, raw_description, industry=None, target_audience=None,
               problem_statement=None, proposed_solution=None, revenue_model=None, is_sample=False):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO startup_ideas (
                    user_id, title, raw_description, industry, target_audience,
                    problem_statement, proposed_solution, revenue_model, status, is_sample
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?)
            """, (
                user_id, title, raw_description, industry, target_audience,
                problem_statement, proposed_solution, revenue_model, 1 if is_sample else 0
            ))
            return cursor.lastrowid

    @classmethod
    def get_by_id(cls, idea_id, user_id=None):
        with get_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM startup_ideas WHERE id = ? AND user_id = ?", (idea_id, user_id))
            else:
                cursor.execute("SELECT * FROM startup_ideas WHERE id = ?", (idea_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['recommendation'] = normalize_recommendation(d.get('recommendation'), d.get('viability_score', 0))
                return d
            return None

    @classmethod
    def get_all_by_user(cls, user_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM startup_ideas
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d['recommendation'] = normalize_recommendation(d.get('recommendation'), d.get('viability_score', 0))
                result.append(d)
            return result

    @classmethod
    def get_recent_by_user(cls, user_id, limit=5):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM startup_ideas
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d['recommendation'] = normalize_recommendation(d.get('recommendation'), d.get('viability_score', 0))
                result.append(d)
            return result

    @classmethod
    def update_extracted_data(cls, idea_id, industry, target_audience, problem_statement, proposed_solution, revenue_model):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE startup_ideas
                SET industry = ?, target_audience = ?, problem_statement = ?,
                    proposed_solution = ?, revenue_model = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (industry, target_audience, problem_statement, proposed_solution, revenue_model, idea_id))

    @classmethod
    def update_status(cls, idea_id, status, viability_score=None, recommendation=None):
        with get_db() as conn:
            cursor = conn.cursor()
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [status]
            if viability_score is not None:
                updates.append("viability_score = ?")
                params.append(viability_score)
            if recommendation is not None:
                updates.append("recommendation = ?")
                params.append(normalize_recommendation(recommendation, viability_score or 0))
            params.append(idea_id)

            cursor.execute(f"UPDATE startup_ideas SET {', '.join(updates)} WHERE id = ?", params)

    @classmethod
    def delete(cls, idea_id, user_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM startup_ideas WHERE id = ? AND user_id = ?", (idea_id, user_id))
            return cursor.rowcount > 0

    @classmethod
    def get_user_stats(cls, user_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ideas,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_validations,
                    AVG(CASE WHEN status = 'completed' THEN viability_score ELSE NULL END) as avg_score,
                    SUM(CASE WHEN viability_score >= 75 THEN 1 ELSE 0 END) as proceed_count,
                    SUM(CASE WHEN viability_score >= 55 AND viability_score < 75 THEN 1 ELSE 0 END) as improve_count,
                    SUM(CASE WHEN viability_score < 55 AND status = 'completed' THEN 1 ELSE 0 END) as reconsider_count,
                    SUM(CASE WHEN viability_score >= 75 THEN 1 ELSE 0 END) as high_potential
                FROM startup_ideas
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            data = dict(row) if row else {}
            return {
                "total_ideas": data.get("total_ideas") or 0,
                "completed_validations": data.get("completed_validations") or 0,
                "avg_score": round(data.get("avg_score") or 0, 1),
                "high_potential": data.get("high_potential") or 0,
                "proceed_count": data.get("proceed_count") or 0,
                "improve_count": data.get("improve_count") or 0,
                "reconsider_count": data.get("reconsider_count") or 0
            }

    @classmethod
    def get_final_verdict(cls, idea_id):
        """Generates comprehensive final startup verdict from actual validation results"""
        idea = cls.get_by_id(idea_id)
        if not idea:
            return None

        analyses = AnalysisResult.get_all_for_idea(idea_id)
        report_data = analyses.get("report", {}).get("data", {})
        swot_risk = analyses.get("swot_risk", {}).get("data", {})
        market_data = analyses.get("market", {}).get("data", {})
        gtm_data = analyses.get("gtm", {}).get("data", {})
        mvp_data = analyses.get("mvp", {}).get("data", {})

        score = idea.get("viability_score") or report_data.get("viability_score") or 75
        rec = normalize_recommendation(report_data.get("recommendation") or idea.get("recommendation"), score)

        # 1. Biggest Strength
        strength = report_data.get("biggest_strength")
        if not strength and report_data.get("key_strengths_summary"):
            strength = report_data["key_strengths_summary"][0]
        if not strength and swot_risk.get("swot", {}).get("strengths"):
            strength = swot_risk["swot"]["strengths"][0]
        if not strength:
            strength = "Proprietary automated workflow delivering measurable time savings and high customer utility."

        # 2. Biggest Weakness / Risk
        weakness = report_data.get("biggest_weakness")
        if not weakness and report_data.get("critical_risks_summary"):
            weakness = report_data["critical_risks_summary"][0]
        if not weakness and swot_risk.get("risks"):
            r0 = swot_risk["risks"][0]
            weakness = r0.get("risk") if isinstance(r0, dict) else str(r0)
        if not weakness and swot_risk.get("swot", {}).get("weaknesses"):
            weakness = swot_risk["swot"]["weaknesses"][0]
        if not weakness:
            weakness = "Customer acquisition cost efficiency and competing against default behavioral inertia."

        # 3. Best Market Opportunity
        opportunity = report_data.get("best_market_opportunity")
        if not opportunity and swot_risk.get("swot", {}).get("opportunities"):
            opportunity = swot_risk["swot"]["opportunities"][0]
        if not opportunity and market_data.get("tam"):
            opportunity = f"Capturing early market share in the {market_data.get('tam')} category expanding at {market_data.get('cagr', '15%+')} CAGR."
        if not opportunity:
            opportunity = "Capturing under-served SMB/mid-market niches overlooked by bloated legacy incumbents."

        # 4. Recommended Next Action for Founder
        action = report_data.get("recommended_next_action")
        if not action and report_data.get("next_immediate_steps"):
            action = report_data["next_immediate_steps"][0]
        if not action:
            if rec == "PROCEED":
                action = "Conduct 15 customer discovery interviews with target ICP and launch a 6-week MVP build of the core loop."
            elif rec == "IMPROVE":
                action = "Refine pricing model and value proposition differentiation before investing in custom engineering."
            else:
                action = "Pivot core solution towards high-urgency pain points where customers demonstrate immediate willingness to pay."

        # 5. Transparent Scoring Rationale
        rationale = report_data.get("scoring_rationale")
        if not rationale:
            if rec == "PROCEED":
                rationale = f"Assigned {score}/100 based on strong market demand ({report_data.get('market_score', 85)}/100), high competitive defensibility ({report_data.get('competition_score', 78)}/100), and manageable risk profile. Recommended for active validation."
            elif rec == "IMPROVE":
                rationale = f"Assigned {score}/100 indicating viable potential but requiring strategic tuning in distribution channels, unit economics, or moat defense."
            else:
                rationale = f"Assigned {score}/100 due to elevated market or technical risks. Recommend significant pivot before allocating capital."

        # 6. Is Demo Data flag
        from config import Config
        is_demo = bool(
            idea.get("is_sample") or 
            Config.DEMO_MODE or 
            (report_data.get("_meta", {}).get("source", "").lower().find("demo") != -1) or
            not Config.GROQ_API_KEY
        )

        # 7. Radar scores
        risk_score = swot_risk.get("overall_risk_score") or report_data.get("risk_score", 35)
        radar_scores = {
            "market": report_data.get("market_score") or 85,
            "competition": report_data.get("competition_score") or 78,
            "execution": report_data.get("execution_score") or 80,
            "business": report_data.get("business_score") or 80,
            "riskResistance": max(10, min(100, 100 - risk_score))
        }

        return {
            "idea_id": idea["id"],
            "title": idea["title"],
            "industry": idea.get("industry") or "Technology",
            "viability_score": score,
            "recommendation": rec,
            "biggest_strength": strength,
            "biggest_weakness": weakness,
            "best_market_opportunity": opportunity,
            "recommended_next_action": action,
            "scoring_rationale": rationale,
            "is_demo": is_demo,
            "radar_scores": radar_scores,
            "market_tam": market_data.get("tam", "$10B+"),
            "defensibility_score": analyses.get("competitors", {}).get("data", {}).get("defensibility_score", 75),
            "created_at": idea.get("created_at")
        }


class AnalysisResult:
    @classmethod
    def save_or_update(cls, idea_id, agent_name, result_data, status='completed', execution_time_sec=0.0):
        result_json = json.dumps(result_data, ensure_ascii=False) if not isinstance(result_data, str) else result_data
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results (idea_id, agent_name, result_json, status, execution_time_sec)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(idea_id, agent_name) DO UPDATE SET
                    result_json = excluded.result_json,
                    status = excluded.status,
                    execution_time_sec = excluded.execution_time_sec,
                    created_at = CURRENT_TIMESTAMP
            """, (idea_id, agent_name, result_json, status, execution_time_sec))

    @classmethod
    def get_by_idea_and_agent(cls, idea_id, agent_name):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_results
                WHERE idea_id = ? AND agent_name = ?
            """, (idea_id, agent_name))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                try:
                    d["data"] = json.loads(d["result_json"])
                except Exception:
                    d["data"] = {}
                return d
        return None

    @classmethod
    def get_all_for_idea(cls, idea_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_results WHERE idea_id = ?", (idea_id,))
            rows = cursor.fetchall()
            results = {}
            for r in rows:
                d = dict(r)
                try:
                    d["data"] = json.loads(d["result_json"])
                except Exception:
                    d["data"] = {}
                results[d["agent_name"]] = d
            return results


class Competitor:
    @classmethod
    def save_batch(cls, idea_id, competitors_list):
        with get_db() as conn:
            cursor = conn.cursor()
            # Clear previous competitors for this idea
            cursor.execute("DELETE FROM competitors WHERE idea_id = ?", (idea_id,))
            for comp in competitors_list:
                feat = comp.get("features") or comp.get("main_features") or ""
                if isinstance(feat, list):
                    feat = ", ".join(feat)
                cursor.execute("""
                    INSERT INTO competitors (
                        idea_id, name, competitor_type, website_url, pricing_model,
                        features, strengths, weaknesses, market_gap, source_reference, verified_source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    idea_id,
                    comp.get("name", "Unknown"),
                    comp.get("competitor_type", "Direct"),
                    comp.get("website_url", ""),
                    comp.get("pricing_model", "Subscription"),
                    feat,
                    comp.get("strengths", ""),
                    comp.get("weaknesses", ""),
                    comp.get("market_gap", ""),
                    comp.get("source_reference", ""),
                    1 if comp.get("verified_source") else 0
                ))

    @classmethod
    def get_by_idea(cls, idea_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM competitors WHERE idea_id = ? ORDER BY id ASC", (idea_id,))
            return [dict(r) for r in cursor.fetchall()]


class ChatMessage:
    @classmethod
    def add_message(cls, idea_id, user_id, role, message):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (idea_id, user_id, role, message)
                VALUES (?, ?, ?, ?)
            """, (idea_id, user_id, role, message))
            return cursor.lastrowid

    @classmethod
    def get_history_for_idea(cls, idea_id, limit=50):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chat_messages
                WHERE idea_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (idea_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def clear_history(cls, idea_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages WHERE idea_id = ?", (idea_id,))


class ValidationReport:
    @classmethod
    def save_report(cls, idea_id, user_id, summary_text, viability_score, market_score,
                    competition_score, execution_score, risk_score, pdf_filename, full_report_data):
        report_json = json.dumps(full_report_data, ensure_ascii=False) if not isinstance(full_report_data, str) else full_report_data
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO validation_reports (
                    idea_id, user_id, summary_text, viability_score, market_score,
                    competition_score, execution_score, risk_score, pdf_filename, full_report_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idea_id, user_id, summary_text, viability_score, market_score,
                competition_score, execution_score, risk_score, pdf_filename, report_json
            ))
            return cursor.lastrowid

    @classmethod
    def get_by_idea(cls, idea_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM validation_reports
                WHERE idea_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (idea_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                try:
                    d["data"] = json.loads(d["full_report_json"])
                except Exception:
                    d["data"] = {}
                return d
        return None
