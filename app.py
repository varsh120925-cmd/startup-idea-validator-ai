import os
import io
import csv
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from config import Config
from database.db import init_db
from database.models import (
    User, StartupIdea, AnalysisResult, Competitor, ChatMessage, ValidationReport
)
from orchestration.pipeline import OrchestrationPipeline
from agents.startup_advisor import StartupAdvisorAgent
from services.groq_service import GroqService
from services.search_service import SearchService
from services.pdf_service import PDFReportService

def create_app(test_config=None):
    """Application factory for Startup Idea Validator AI"""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Please sign in to access your startup dashboard."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Initialize Database Schema
    with app.app_context():
        init_db()

    # Context processor to inject global parameters
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now().year,
            "demo_mode": Config.DEMO_MODE,
            "groq_configured": bool(Config.GROQ_API_KEY),
            "tavily_configured": bool(Config.TAVILY_API_KEY),
            "selected_model": Config.GROQ_MODEL
        }

    # =========================================================================
    # 1. AUTHENTICATION ROUTES (Page 1)
    # =========================================================================
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            remember = bool(request.form.get("remember"))

            user = User.get_by_email(email)
            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash(f"Welcome back, {user.full_name or user.username}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("dashboard"))
            else:
                flash("Invalid email address or password. Please try again.", "danger")

        return render_template("auth/login.html")

    @app.route("/demo-login")
    def demo_login():
        """1-click instant login helper for judges and reviewers"""
        demo_user = User.get_by_email("demo@startupvalidator.com")
        if not demo_user:
            demo_user = User.create(
                username="demofounder",
                email="demo@startupvalidator.com",
                password="password123",
                full_name="Alex Rivera (Founder)"
            )
        login_user(demo_user)
        flash("Logged in with Founder Demo Account. Welcome!", "success")
        return redirect(url_for("dashboard"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            if not email or not username or not password:
                flash("All required fields must be filled.", "warning")
                return render_template("auth/register.html")

            if password != confirm:
                flash("Passwords do not match.", "warning")
                return render_template("auth/register.html")

            if User.get_by_email(email):
                flash("An account with that email already exists.", "danger")
                return render_template("auth/register.html")

            if User.get_by_username(username):
                flash("That username is already taken. Please choose another.", "danger")
                return render_template("auth/register.html")

            new_user = User.create(username, email, password, full_name=full_name)
            login_user(new_user)
            flash("Account created successfully! Welcome to your Startup Validator.", "success")
            return redirect(url_for("dashboard"))

        return render_template("auth/register.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have signed out successfully.", "info")
        return redirect(url_for("login"))

    # =========================================================================
    # 2. MAIN DASHBOARD (Page 2)
    # =========================================================================
    @app.route("/dashboard")
    @login_required
    def dashboard():
        selected_id = request.args.get("idea_id", type=int)
        stats = StartupIdea.get_user_stats(current_user.id)
        recent_ideas = StartupIdea.get_recent_by_user(current_user.id, limit=6)
        all_ideas = StartupIdea.get_all_by_user(current_user.id)

        # Determine which idea to display final verdict & insights for
        active_idea = None
        if selected_id:
            active_idea = StartupIdea.get_by_id(selected_id, current_user.id)
        if not active_idea and recent_ideas:
            active_idea = recent_ideas[0]

        latest_verdict = None
        active_analyses = {}
        if active_idea:
            latest_verdict = StartupIdea.get_final_verdict(active_idea["id"])
            active_analyses = AnalysisResult.get_all_for_idea(active_idea["id"])

        return render_template(
            "dashboard/index.html",
            stats=stats,
            recent_ideas=recent_ideas,
            all_ideas=all_ideas,
            active_idea=active_idea,
            latest_verdict=latest_verdict,
            active_analyses=active_analyses
        )

    # =========================================================================
    # 3. STARTUP IDEA SUBMISSION (Page 3)
    # =========================================================================
    @app.route("/submit", methods=["GET", "POST"])
    @login_required
    def submit_idea():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            industry = request.form.get("industry", "").strip()
            raw_description = request.form.get("raw_description", "").strip()
            target_audience = request.form.get("target_audience", "").strip()
            problem_statement = request.form.get("problem_statement", "").strip()
            proposed_solution = request.form.get("proposed_solution", "").strip()
            revenue_model = request.form.get("revenue_model", "").strip()
            run_async_flag = request.form.get("run_async", "true") == "true"

            if not title or not raw_description:
                flash("Please provide at least an Idea Title and a Description.", "warning")
                return render_template("dashboard/submit.html")

            idea_id = StartupIdea.create(
                user_id=current_user.id,
                title=title,
                raw_description=raw_description,
                industry=industry,
                target_audience=target_audience,
                problem_statement=problem_statement,
                proposed_solution=proposed_solution,
                revenue_model=revenue_model
            )

            flash(f"Startup idea '{title}' submitted! AI validation agents are starting analysis.", "success")

            # Kick off validation
            pipeline = OrchestrationPipeline(idea_id=idea_id, user_id=current_user.id)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                pipeline.run_async()
                return jsonify({
                    "status": "started",
                    "idea_id": idea_id,
                    "redirect_url": url_for("view_report", idea_id=idea_id)
                })

            if run_async_flag:
                pipeline.run_async()
                return redirect(url_for("view_market", idea_id=idea_id, validated="started"))
            else:
                try:
                    pipeline.run_synchronous()
                    return redirect(url_for("view_report", idea_id=idea_id))
                except Exception as e:
                    flash(f"Error during validation: {e}", "danger")
                    return redirect(url_for("dashboard"))

        return render_template("dashboard/submit.html")

    # =========================================================================
    # 4. MARKET OPPORTUNITY ANALYSIS (Page 4)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/market")
    @login_required
    def view_market(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        market_res = analyses.get("market", {})
        extractor_res = analyses.get("extractor", {})
        return render_template(
            "dashboard/market.html",
            idea=idea,
            market=market_res.get("data", {}),
            extractor=extractor_res.get("data", {}),
            analyses=analyses
        )

    # =========================================================================
    # 5. COMPETITOR ANALYSIS (Page 5)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/competitors")
    @login_required
    def view_competitors(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        competitors = Competitor.get_by_idea(idea_id)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        comp_agent_data = analyses.get("competitors", {}).get("data", {})
        return render_template(
            "dashboard/competitors.html",
            idea=idea,
            competitors=competitors,
            comp_data=comp_agent_data,
            analyses=analyses
        )

    # =========================================================================
    # 6. SWOT ANALYSIS (Page 6)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/swot")
    @login_required
    def view_swot(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        swot_data = analyses.get("swot_risk", {}).get("data", {}).get("swot", {})
        return render_template(
            "dashboard/swot.html",
            idea=idea,
            swot=swot_data,
            analyses=analyses
        )

    # =========================================================================
    # 7. RISK ANALYSIS (Page 7)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/risks")
    @login_required
    def view_risks(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        swot_risk_res = analyses.get("swot_risk", {}).get("data", {})
        risks = swot_risk_res.get("risks", [])
        overall_risk_score = swot_risk_res.get("overall_risk_score", 35)
        risk_rating = swot_risk_res.get("risk_rating", "Moderate Risk")
        return render_template(
            "dashboard/risks.html",
            idea=idea,
            risks=risks,
            overall_risk_score=overall_risk_score,
            risk_rating=risk_rating,
            founder_advice=swot_risk_res.get("founder_advice", ""),
            analyses=analyses
        )

    # =========================================================================
    # 8. MVP FEATURE RECOMMENDATIONS (Page 8)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/mvp")
    @login_required
    def view_mvp(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        mvp_data = analyses.get("mvp", {}).get("data", {})
        return render_template(
            "dashboard/mvp.html",
            idea=idea,
            mvp=mvp_data,
            analyses=analyses
        )

    # =========================================================================
    # 9. GO-TO-MARKET STRATEGY (Page 9)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/gtm")
    @login_required
    def view_gtm(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        gtm_data = analyses.get("gtm", {}).get("data", {})
        return render_template(
            "dashboard/gtm.html",
            idea=idea,
            gtm=gtm_data,
            analyses=analyses
        )

    # =========================================================================
    # 10. AI STARTUP ADVISOR CHATBOT (Page 10)
    # =========================================================================
    @app.route("/advisor")
    @login_required
    def general_advisor():
        ideas = StartupIdea.get_all_by_user(current_user.id)
        if ideas:
            return redirect(url_for("view_chat", idea_id=ideas[0]["id"]))
        flash("Please submit or generate a startup idea first to chat with the AI Advisor.", "info")
        return redirect(url_for("submit_idea"))

    @app.route("/idea/<int:idea_id>/chat")
    @login_required
    def view_chat(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        all_ideas = StartupIdea.get_all_by_user(current_user.id)
        chat_history = ChatMessage.get_history_for_idea(idea_id)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        return render_template(
            "dashboard/chat.html",
            idea=idea,
            all_ideas=all_ideas,
            chat_history=chat_history,
            analyses=analyses
        )

    # =========================================================================
    # 11. VALIDATION HISTORY (Page 11)
    # =========================================================================
    @app.route("/history")
    @login_required
    def view_history():
        ideas = StartupIdea.get_all_by_user(current_user.id)
        return render_template("dashboard/history.html", ideas=ideas)

    # =========================================================================
    # 12. FINAL REPORT GENERATION (Page 12)
    # =========================================================================
    @app.route("/idea/<int:idea_id>/report")
    @login_required
    def view_report(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        competitors = Competitor.get_by_idea(idea_id)
        report_record = ValidationReport.get_by_idea(idea_id)
        report_data = analyses.get("report", {}).get("data", {})
        return render_template(
            "dashboard/report.html",
            idea=idea,
            analyses=analyses,
            competitors=competitors,
            report_record=report_record,
            report_data=report_data
        )

    # =========================================================================
    # 13. SETTINGS & PROFILE (Page 13)
    # =========================================================================
    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def view_settings():
        if request.method == "POST":
            groq_key = request.form.get("groq_api_key", "").strip()
            tavily_key = request.form.get("tavily_api_key", "").strip()
            groq_model = request.form.get("groq_model", "llama-3.3-70b-versatile").strip()
            demo_mode = request.form.get("demo_mode") == "on"

            Config.update_runtime_keys(
                groq_key=groq_key if groq_key else Config.GROQ_API_KEY,
                tavily_key=tavily_key if tavily_key else Config.TAVILY_API_KEY,
                model=groq_model,
                demo_mode=demo_mode
            )

            flash("Settings and API configuration updated successfully!", "success")
            return redirect(url_for("view_settings"))

        return render_template(
            "dashboard/settings.html",
            models=Config.AVAILABLE_MODELS,
            current_model=Config.GROQ_MODEL,
            groq_key_set=bool(Config.GROQ_API_KEY),
            tavily_key_set=bool(Config.TAVILY_API_KEY),
            demo_mode=Config.DEMO_MODE
        )

    # =========================================================================
    # API ENDPOINTS (Asynchronous Pipeline, Chat, Status, Exports)
    # =========================================================================
    @app.route("/api/idea/<int:idea_id>/status")
    @login_required
    def api_idea_status(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            return jsonify({"status": "error", "message": "Idea not found"}), 404
        progress = OrchestrationPipeline.get_progress(idea_id)
        verdict = StartupIdea.get_final_verdict(idea_id) if idea.get("status") == "completed" else None
        return jsonify({
            "idea_id": idea_id,
            "status": idea.get("status"),
            "viability_score": idea.get("viability_score"),
            "recommendation": idea.get("recommendation"),
            "progress": progress,
            "verdict": verdict
        })

    @app.route("/api/idea/<int:idea_id>/run", methods=["POST"])
    @login_required
    def api_trigger_validation(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            return jsonify({"status": "error", "message": "Idea not found"}), 404
        pipeline = OrchestrationPipeline(idea_id=idea_id, user_id=current_user.id)
        pipeline.run_async()
        return jsonify({"status": "started", "message": "Validation pipeline initiated."})

    @app.route("/api/idea/<int:idea_id>/chat", methods=["POST"])
    @login_required
    def api_chat(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            return jsonify({"status": "error", "message": "Idea not found"}), 404

        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        # Save user message
        ChatMessage.add_message(idea_id=idea_id, user_id=current_user.id, role="user", message=user_message)

        # Retrieve analysis context
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        history = ChatMessage.get_history_for_idea(idea_id)

        # Execute advisor
        advisor = StartupAdvisorAgent()
        reply_dict = advisor.answer_query(
            user_query=user_message,
            idea_dict=idea,
            analysis_dict=analyses,
            conversation_history=history
        )

        assistant_reply = reply_dict.get("reply", "I am analyzing your startup metrics.")

        # Save assistant message
        ChatMessage.add_message(idea_id=idea_id, user_id=current_user.id, role="assistant", message=assistant_reply)

        return jsonify({
            "status": "success",
            "reply": assistant_reply,
            "source": reply_dict.get("source", "AI Startup Advisor")
        })

    @app.route("/api/idea/<int:idea_id>/chat/clear", methods=["POST"])
    @login_required
    def api_clear_chat(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            return jsonify({"status": "error", "message": "Idea not found"}), 404
        ChatMessage.clear_history(idea_id)
        return jsonify({"status": "success", "message": "Chat history cleared."})

    @app.route("/api/idea/<int:idea_id>/delete", methods=["POST"])
    @login_required
    def api_delete_idea(idea_id):
        success = StartupIdea.delete(idea_id, current_user.id)
        if success:
            flash("Startup idea deleted successfully.", "info")
            return redirect(url_for("view_history"))
        flash("Could not delete idea or unauthorized.", "danger")
        return redirect(url_for("view_history"))

    @app.route("/api/export/<int:idea_id>/pdf")
    @login_required
    def export_pdf(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        competitors = Competitor.get_by_idea(idea_id)
        report_record = ValidationReport.get_by_idea(idea_id)

        # If PDF file already exists on disk, send it
        if report_record and report_record.get("pdf_filename"):
            filepath = os.path.join(Config.EXPORTS_DIR, report_record.get("pdf_filename"))
            if os.path.exists(filepath):
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"Validation_Report_{idea.get('title', 'Startup')}.pdf",
                    mimetype="application/pdf"
                )

        # Generate on the fly
        pdf_bytes = PDFReportService.generate_report(
            idea=idea,
            analysis_dict=analyses,
            competitors=competitors,
            report_meta=report_record or {}
        )
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment;filename=Validation_Report_{idea.get('title', 'Startup')}.pdf"}
        )

    @app.route("/api/export/<int:idea_id>/json")
    @login_required
    def export_json(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        competitors = Competitor.get_by_idea(idea_id)
        report = ValidationReport.get_by_idea(idea_id)

        export_payload = {
            "startup_idea": idea,
            "analyses": analyses,
            "competitors": competitors,
            "validation_report": report,
            "exported_at": datetime.now().isoformat(),
            "export_source": "Startup Idea Validator AI"
        }
        return Response(
            json.dumps(export_payload, indent=2, ensure_ascii=False),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=Startup_Validation_{idea_id}.json"}
        )

    @app.route("/api/export/<int:idea_id>/markdown")
    @login_required
    def export_markdown(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        competitors = Competitor.get_by_idea(idea_id)
        market = analyses.get("market", {}).get("data", {})
        swot = analyses.get("swot_risk", {}).get("data", {}).get("swot", {})
        risks = analyses.get("swot_risk", {}).get("data", {}).get("risks", [])
        mvp = analyses.get("mvp", {}).get("data", {})
        gtm = analyses.get("gtm", {}).get("data", {})

        md = f"""# Startup Validation Report: {idea.get('title')}
**Industry:** {idea.get('industry', 'Technology')}  
**Viability Score:** {idea.get('viability_score', 0)}/100 ({idea.get('recommendation', 'Pending')})  
**Date:** {datetime.now().strftime('%B %d, %Y')}

---

## 1. Executive Summary & Problem-Solution Fit
**Problem Statement:**  
{idea.get('problem_statement') or idea.get('raw_description')}

**Proposed Solution:**  
{idea.get('proposed_solution', 'Automated intelligent workflow.')}

**Target Audience:** {idea.get('target_audience', 'B2B/B2C')}  
**Revenue Model:** {idea.get('revenue_model', 'Subscription SaaS')}  

---

## 2. Market Opportunity
- **Total Addressable Market (TAM):** {market.get('tam', 'N/A')}
- **Serviceable Addressable Market (SAM):** {market.get('sam', 'N/A')}
- **Serviceable Obtainable Market (SOM):** {market.get('som', 'N/A')}
- **Market Growth (CAGR):** {market.get('cagr', 'N/A')}

---

## 3. Competitor Landscape
"""
        for c in competitors:
            md += f"- **{c.get('name')}** ({c.get('competitor_type')}): {c.get('pricing_model')} | Market Gap: {c.get('market_gap')}\n"

        md += "\n---\n\n## 4. SWOT Strategic Matrix\n"
        md += f"**Strengths:** {', '.join(swot.get('strengths', []))}\n\n"
        md += f"**Weaknesses:** {', '.join(swot.get('weaknesses', []))}\n\n"
        md += f"**Opportunities:** {', '.join(swot.get('opportunities', []))}\n\n"
        md += f"**Threats:** {', '.join(swot.get('threats', []))}\n\n"

        md += "\n---\n\n## 5. MVP Feature Scope\n"
        for m in mvp.get("must_have", []):
            md += f"- [x] **Must-Have:** {m}\n"
        for s in mvp.get("should_have", []):
            md += f"- [ ] **Should-Have:** {s}\n"

        md += f"\n---\n\n## 6. Go-to-Market Strategy\n"
        md += f"**Positioning Statement:**\n{gtm.get('positioning_statement', 'N/A')}\n\n"
        md += f"**Target Channels:**\n"
        for ch in gtm.get("acquisition_channels", []):
            md += f"- {ch}\n"

        return Response(
            md,
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment;filename=Validation_Report_{idea_id}.md"}
        )

    @app.route("/api/export/<int:idea_id>/csv")
    @login_required
    def export_csv(idea_id):
        idea = StartupIdea.get_by_id(idea_id, current_user.id)
        if not idea:
            abort(404)
        analyses = AnalysisResult.get_all_for_idea(idea_id)
        competitors = Competitor.get_by_idea(idea_id)
        verdict = StartupIdea.get_final_verdict(idea_id)
        mvp_data = analyses.get("mvp", {}).get("data", {})
        weekly = mvp_data.get("weekly_milestones", [])

        output = io.StringIO()
        writer = csv.writer(output)

        # 1. Startup Overview & Verdict
        writer.writerow(["=== STARTUP IDEA VALIDATION REPORT ==="])
        writer.writerow(["Title", idea.get("title", "")])
        writer.writerow(["Industry", idea.get("industry", "")])
        writer.writerow(["Viability Score", f"{verdict.get('viability_score', 0)}/100"])
        writer.writerow(["Final Recommendation", verdict.get("recommendation", "N/A")])
        writer.writerow(["Biggest Strength", verdict.get("biggest_strength", "")])
        writer.writerow(["Biggest Weakness", verdict.get("biggest_weakness", "")])
        writer.writerow(["Best Market Opportunity", verdict.get("best_market_opportunity", "")])
        writer.writerow(["Recommended Next Action", verdict.get("recommended_next_action", "")])
        writer.writerow(["Data Mode", "DEMO DATA" if verdict.get("is_demo") else "VERIFIED LIVE DATA"])
        writer.writerow([])

        # 2. Market Sizing
        market_data = analyses.get("market", {}).get("data", {})
        writer.writerow(["=== MARKET SIZING ==="])
        writer.writerow(["TAM", market_data.get("tam", "")])
        writer.writerow(["SAM", market_data.get("sam", "")])
        writer.writerow(["SOM", market_data.get("som", "")])
        writer.writerow(["CAGR", market_data.get("cagr", "")])
        writer.writerow([])

        # 3. Competitor Comparison
        writer.writerow(["=== COMPETITOR COMPARISON TABLE ==="])
        writer.writerow(["Name", "Type", "Pricing", "Features", "Strengths", "Weaknesses", "Market Gap", "Source"])
        for c in competitors:
            feats = c.get("features", "")
            if isinstance(feats, list):
                feats = "; ".join(feats)
            writer.writerow([
                c.get("name", ""),
                c.get("competitor_type", ""),
                c.get("pricing") or c.get("pricing_model", ""),
                feats,
                c.get("strengths", ""),
                c.get("weaknesses", ""),
                c.get("market_gap", ""),
                c.get("source_url", "")
            ])
        writer.writerow([])

        # 4. MVP 6-Week Roadmap
        writer.writerow(["=== 6-WEEK MVP DEVELOPMENT ROADMAP ==="])
        writer.writerow(["Week", "Phase", "Core Focus", "Deliverables", "Status", "Progress %"])
        for m in weekly:
            deliv = m.get("deliverables", [])
            if isinstance(deliv, list):
                deliv = "; ".join(deliv)
            writer.writerow([
                m.get("week", ""),
                m.get("phase", ""),
                m.get("focus", ""),
                deliv,
                m.get("status", ""),
                m.get("progress_pct", 0)
            ])
        writer.writerow([])

        # 5. SWOT Analysis
        swot_data = analyses.get("swot_risk", {}).get("data", {}).get("swot", {})
        writer.writerow(["=== SWOT STRATEGIC MATRIX ==="])
        writer.writerow(["Strengths", "; ".join(swot_data.get("strengths", []))])
        writer.writerow(["Weaknesses", "; ".join(swot_data.get("weaknesses", []))])
        writer.writerow(["Opportunities", "; ".join(swot_data.get("opportunities", []))])
        writer.writerow(["Threats", "; ".join(swot_data.get("threats", []))])

        safe_title = "".join(c for c in idea.get("title", "startup") if c.isalnum() or c in (' ', '_', '-')).strip()
        filename = f"Validation_{safe_title}_{idea_id}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    @app.route("/api/ideas/compare")
    @login_required
    def api_compare_ideas():
        id1 = request.args.get("id1", type=int)
        id2 = request.args.get("id2", type=int)
        if not id1 or not id2:
            return jsonify({"status": "error", "message": "Both id1 and id2 are required"}), 400

        idea1 = StartupIdea.get_by_id(id1, current_user.id)
        idea2 = StartupIdea.get_by_id(id2, current_user.id)
        if not idea1 or not idea2:
            return jsonify({"status": "error", "message": "One or both ideas not found"}), 404

        v1 = StartupIdea.get_final_verdict(id1)
        v2 = StartupIdea.get_final_verdict(id2)
        analyses1 = AnalysisResult.get_all_for_idea(id1)
        analyses2 = AnalysisResult.get_all_for_idea(id2)
        comps1 = Competitor.get_by_idea(id1)
        comps2 = Competitor.get_by_idea(id2)

        return jsonify({
            "status": "success",
            "idea1": {
                "id": idea1["id"],
                "title": idea1["title"],
                "industry": idea1.get("industry"),
                "created_at": str(idea1.get("created_at")),
                "verdict": v1,
                "competitor_count": len(comps1),
                "tam": analyses1.get("market", {}).get("data", {}).get("tam", "N/A"),
                "cagr": analyses1.get("market", {}).get("data", {}).get("cagr", "N/A"),
                "strengths": analyses1.get("swot_risk", {}).get("data", {}).get("swot", {}).get("strengths", [])[:3],
                "risks": [r.get("risk") if isinstance(r, dict) else str(r) for r in analyses1.get("swot_risk", {}).get("data", {}).get("risks", [])[:3]]
            },
            "idea2": {
                "id": idea2["id"],
                "title": idea2["title"],
                "industry": idea2.get("industry"),
                "created_at": str(idea2.get("created_at")),
                "verdict": v2,
                "competitor_count": len(comps2),
                "tam": analyses2.get("market", {}).get("data", {}).get("tam", "N/A"),
                "cagr": analyses2.get("market", {}).get("data", {}).get("cagr", "N/A"),
                "strengths": analyses2.get("swot_risk", {}).get("data", {}).get("swot", {}).get("strengths", [])[:3],
                "risks": [r.get("risk") if isinstance(r, dict) else str(r) for r in analyses2.get("swot_risk", {}).get("data", {}).get("risks", [])[:3]]
            }
        })

    @app.route("/api/settings/test-groq")
    @login_required
    def api_test_groq():
        service = GroqService()
        success, message = service.test_connection()
        return jsonify({"success": success, "message": message})

    @app.route("/api/settings/test-tavily")
    @login_required
    def api_test_tavily():
        service = SearchService()
        success, message = service.test_connection()
        return jsonify({"success": success, "message": message})

    @app.route("/api/sample/load", methods=["POST"])
    @login_required
    def api_load_sample_data():
        """
        Seeds 2 rich, realistic sample ideas with full multi-agent validation completed
        so the user can immediately explore charts, reports, chat, and competitor tables.
        Clearly tagged as sample data as required by Instruction 11.
        """
        # Sample Idea 1: LexiDraft AI (LegalTech)
        idea1_id = StartupIdea.create(
            user_id=current_user.id,
            title="LexiDraft AI — Freelancer Contract Copilot",
            raw_description=(
                "An AI assistant designed for freelance software developers and independent designers "
                "that reviews client master service agreements, highlights unfair indemnification clauses, "
                "and generates polite counter-proposal emails to protect payment terms."
            ),
            industry="LegalTech / Productivity SaaS",
            target_audience="Freelance developers, independent designers, boutique digital agencies",
            problem_statement="Independent knowledge workers frequently sign disadvantageous contracts with vague scope and one-sided indemnification clauses because hiring a contract lawyer costs $400/hr.",
            proposed_solution="An instant document redlining copilot that translates legalese into plain English risk scores, alerts on hidden liabilities, and auto-generates negotiated clause edits.",
            revenue_model="Freemium + $29/mo Pro or $199/yr Unlimited",
            is_sample=True
        )

        pipeline1 = OrchestrationPipeline(idea_id=idea1_id, user_id=current_user.id)
        pipeline1.run_synchronous()

        # Sample Idea 2: CarbonTrace (ClimateTech)
        idea2_id = StartupIdea.create(
            user_id=current_user.id,
            title="CarbonTrace — Automated Scope 3 Carbon Accounting",
            raw_description=(
                "A lightweight B2B carbon accounting software for mid-market manufacturing suppliers "
                "that automatically ingests utility bills, ERP supplier receipts, and logistics manifests "
                "to generate certified ESG emissions reports for enterprise enterprise buyers."
            ),
            industry="ClimateTech / Enterprise ESG",
            target_audience="Mid-market manufacturers, logistics fleets, Tier-1 supply chain contractors",
            problem_statement="Mid-sized suppliers are being pressured by enterprise customers (Apple, Walmart) to disclose Scope 3 emissions under CSRD/SEC rules, but lack the resources for $50k consulting audits.",
            proposed_solution="Plug-and-play carbon telemetry platform that connects directly to QuickBooks, SAP, and fleet fuel telemetry to produce audit-ready GHG Protocol carbon footprints within 48 hours.",
            revenue_model="Tiered B2B SaaS ($299/mo Starter, $899/mo Growth)",
            is_sample=True
        )

        pipeline2 = OrchestrationPipeline(idea_id=idea2_id, user_id=current_user.id)
        pipeline2.run_synchronous()

        flash("Loaded 2 comprehensive sample startup validations (clearly marked as Sample Data)!", "success")
        return redirect(url_for("dashboard"))

    return app

if __name__ == "__main__":
    application = create_app()
    application.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
