import time
import logging
import threading
from database.models import StartupIdea, AnalysisResult, Competitor, ValidationReport
from agents.idea_extractor import IdeaExtractionAgent
from agents.market_analyzer import MarketAnalyzerAgent
from agents.competitor_agent import CompetitorDiscoveryAgent
from agents.swot_risk_agent import SWOTRiskAgent
from agents.mvp_recommender import MVPRecommenderAgent
from agents.gtm_strategist import GTMStrategistAgent
from agents.startup_advisor import StartupAdvisorAgent
from agents.report_generator import ReportGeneratorAgent
from .context_store import ContextStore

logger = logging.getLogger(__name__)

# Global in-memory dictionary for real-time progress monitoring
_ACTIVE_PIPELINES = {}

class OrchestrationPipeline:
    """Central orchestration system coordinating the sequential 8-agent validation pipeline"""

    AGENTS_METADATA = [
        {"id": "extractor", "name": "Idea Extractor", "icon": "bi-lightbulb-fill", "desc": "Structuring business concept, problem, and solution..."},
        {"id": "market", "name": "Market Analyzer", "icon": "bi-pie-chart-fill", "desc": "Estimating TAM/SAM/SOM and segmenting audience..."},
        {"id": "competitors", "name": "Competitor Agent", "icon": "bi-binoculars-fill", "desc": "Searching web for competitors and identifying gaps..."},
        {"id": "swot_risk", "name": "SWOT & Risk Agent", "icon": "bi-shield-shaded", "desc": "Evaluating strengths, threats, and mitigation playbook..."},
        {"id": "mvp", "name": "MVP Recommender", "icon": "bi-layers-fill", "desc": "Formulating MoSCoW prioritization and 6-week milestones..."},
        {"id": "gtm", "name": "Go-to-Market Strategist", "icon": "bi-graph-up-arrow", "desc": "Drafting positioning, pricing tiers, and 90-day roadmap..."},
        {"id": "advisor", "name": "Startup Advisor", "icon": "bi-chat-square-dots-fill", "desc": "Synthesizing executive advisory brief and guidance..."},
        {"id": "report", "name": "Report Generator", "icon": "bi-file-earmark-pdf-fill", "desc": "Synthesizing final startup verdict and compiling PDF..."}
    ]

    def __init__(self, idea_id, user_id=None):
        self.idea_id = idea_id
        self.user_id = user_id
        self.context_store = ContextStore()

    @classmethod
    def get_progress(cls, idea_id):
        """
        Returns real execution progress for an idea.
        If running in memory, returns live agent status.
        If loaded from database, reconstructs real agent states from analysis_results.
        """
        if idea_id in _ACTIVE_PIPELINES:
            return _ACTIVE_PIPELINES[idea_id]

        # Reconstruct real status from database records
        idea = StartupIdea.get_by_id(idea_id)
        if not idea:
            return {
                "percent": 0,
                "current_step": "idle",
                "message": "Ready to validate",
                "status": "idle",
                "agents": {meta["id"]: {"id": meta["id"], "name": meta["name"], "status": "pending", "time": 0.0, "icon": meta["icon"]} for meta in cls.AGENTS_METADATA}
            }

        saved_results = AnalysisResult.get_all_for_idea(idea_id)
        is_completed = (idea.get("status") == "completed")
        is_failed = (idea.get("status") == "failed")

        agents_status = {}
        completed_count = 0

        for meta in cls.AGENTS_METADATA:
            agent_id = meta["id"]
            if agent_id in saved_results:
                rec = saved_results[agent_id]
                agents_status[agent_id] = {
                    "id": agent_id,
                    "name": meta["name"],
                    "icon": meta["icon"],
                    "status": "completed",
                    "time": round(rec.get("execution_time_sec", 0.0), 2),
                    "message": "Analysis completed"
                }
                completed_count += 1
            else:
                agents_status[agent_id] = {
                    "id": agent_id,
                    "name": meta["name"],
                    "icon": meta["icon"],
                    "status": "failed" if is_failed else ("completed" if is_completed else "pending"),
                    "time": 0.0,
                    "message": "Analysis completed" if is_completed else "Pending analysis"
                }

        percent = 100 if is_completed else int(round((completed_count / len(cls.AGENTS_METADATA)) * 100))

        return {
            "percent": percent,
            "current_step": "completed" if is_completed else ("error" if is_failed else "analyzing"),
            "message": "Validation complete! All 8 agents finished." if is_completed else f"{completed_count}/8 agents completed",
            "status": "completed" if is_completed else ("failed" if is_failed else "processing"),
            "agents": agents_status,
            "viability_score": idea.get("viability_score"),
            "recommendation": idea.get("recommendation")
        }

    def _init_pipeline_state(self):
        """Initializes in-memory progress structure tracking all 8 agents"""
        agents_dict = {}
        for meta in self.AGENTS_METADATA:
            agents_dict[meta["id"]] = {
                "id": meta["id"],
                "name": meta["name"],
                "icon": meta["icon"],
                "status": "pending",
                "time": 0.0,
                "message": "Pending"
            }

        _ACTIVE_PIPELINES[self.idea_id] = {
            "percent": 5,
            "current_step": "init",
            "message": "Initializing 8-agent validation pipeline...",
            "status": "processing",
            "agents": agents_dict
        }

    def _update_agent_progress(self, agent_id, status, percent, message=None, elapsed=0.0):
        """Updates real-time progress for a specific agent"""
        if self.idea_id in _ACTIVE_PIPELINES:
            p = _ACTIVE_PIPELINES[self.idea_id]
            p["percent"] = percent
            p["current_step"] = agent_id
            if message:
                p["message"] = message
            if agent_id in p["agents"]:
                p["agents"][agent_id]["status"] = status
                if elapsed > 0:
                    p["agents"][agent_id]["time"] = elapsed
                if message:
                    p["agents"][agent_id]["message"] = message

    def run_synchronous(self):
        """Executes all 8 specialized agents in strict sequence and records results"""
        idea = StartupIdea.get_by_id(self.idea_id)
        if not idea:
            raise ValueError(f"Startup idea ID {self.idea_id} not found.")

        self._init_pipeline_state()
        StartupIdea.update_status(self.idea_id, "analyzing")

        # Load initial context
        self.context_store.update({
            "idea_id": self.idea_id,
            "user_id": idea.get("user_id"),
            "title": idea.get("title"),
            "raw_description": idea.get("raw_description"),
            "industry": idea.get("industry")
        })

        analysis_dict = {}

        try:
            # ----------------------------------------------------
            # AGENT 1: IDEA EXTRACTION
            # ----------------------------------------------------
            self._update_agent_progress("extractor", "processing", 12, "Agent 1: Structuring business model parameters...")
            t0 = time.time()
            extractor_agent = IdeaExtractionAgent()
            extractor_res = extractor_agent.run(self.context_store.to_dict())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("extractor_data", extractor_res)
            analysis_dict["extractor"] = {"data": extractor_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="extractor",
                result_data=extractor_res,
                execution_time_sec=elapsed
            )

            # Update idea record with extracted fields
            StartupIdea.update_extracted_data(
                idea_id=self.idea_id,
                industry=extractor_res.get("industry") or idea.get("industry"),
                target_audience=extractor_res.get("target_audience"),
                problem_statement=extractor_res.get("problem_statement"),
                proposed_solution=extractor_res.get("proposed_solution"),
                revenue_model=extractor_res.get("revenue_model")
            )
            self._update_agent_progress("extractor", "completed", 15, "Agent 1 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 2: MARKET OPPORTUNITY & CUSTOMER SEGMENTATION
            # ----------------------------------------------------
            self._update_agent_progress("market", "processing", 25, "Agent 2: Researching market size, TAM/SAM/SOM, and personas...")
            t0 = time.time()
            market_agent = MarketAnalyzerAgent()
            market_res = market_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("market_data", market_res)
            analysis_dict["market"] = {"data": market_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="market",
                result_data=market_res,
                execution_time_sec=elapsed
            )
            self._update_agent_progress("market", "completed", 30, "Agent 2 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 3: COMPETITOR DISCOVERY & COMPARISON
            # ----------------------------------------------------
            self._update_agent_progress("competitors", "processing", 42, "Agent 3: Crawling web intelligence for competitors and gaps...")
            t0 = time.time()
            competitor_agent = CompetitorDiscoveryAgent()
            competitor_res = competitor_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("competitor_data", competitor_res)
            analysis_dict["competitors"] = {"data": competitor_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="competitors",
                result_data=competitor_res,
                execution_time_sec=elapsed
            )

            # Save competitors to dedicated database table
            raw_comp_list = competitor_res.get("competitors", [])
            Competitor.save_batch(self.idea_id, raw_comp_list)
            self._update_agent_progress("competitors", "completed", 48, "Agent 3 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 4: SWOT & RISK ANALYSIS
            # ----------------------------------------------------
            self._update_agent_progress("swot_risk", "processing", 58, "Agent 4: Evaluating SWOT quadrant factors and assessing risk severity...")
            t0 = time.time()
            swot_agent = SWOTRiskAgent()
            swot_res = swot_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("swot_data", swot_res)
            analysis_dict["swot_risk"] = {"data": swot_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="swot_risk",
                result_data=swot_res,
                execution_time_sec=elapsed
            )
            self._update_agent_progress("swot_risk", "completed", 65, "Agent 4 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 5: MVP FEATURE SCOPING & TIMELINE
            # ----------------------------------------------------
            self._update_agent_progress("mvp", "processing", 74, "Agent 5: Prioritizing MoSCoW MVP features and 6-week milestones...")
            t0 = time.time()
            mvp_agent = MVPRecommenderAgent()
            mvp_res = mvp_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("mvp_data", mvp_res)
            analysis_dict["mvp"] = {"data": mvp_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="mvp",
                result_data=mvp_res,
                execution_time_sec=elapsed
            )
            self._update_agent_progress("mvp", "completed", 78, "Agent 5 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 6: GO-TO-MARKET STRATEGY
            # ----------------------------------------------------
            self._update_agent_progress("gtm", "processing", 84, "Agent 6: Formulating customer acquisition funnels, pricing, and launch plan...")
            t0 = time.time()
            gtm_agent = GTMStrategistAgent()
            gtm_res = gtm_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("gtm_data", gtm_res)
            analysis_dict["gtm"] = {"data": gtm_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="gtm",
                result_data=gtm_res,
                execution_time_sec=elapsed
            )
            self._update_agent_progress("gtm", "completed", 88, "Agent 6 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 7: STARTUP ADVISOR (EXECUTIVE ADVISORY BRIEF)
            # ----------------------------------------------------
            self._update_agent_progress("advisor", "processing", 92, "Agent 7: Synthesizing executive strategic advisory guidance...")
            t0 = time.time()
            advisor_agent = StartupAdvisorAgent()
            advisor_res = advisor_agent.run(self.context_store.get_summary_context())
            elapsed = round(time.time() - t0, 2)
            self.context_store.set("advisor_data", advisor_res)
            analysis_dict["advisor"] = {"data": advisor_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="advisor",
                result_data=advisor_res,
                execution_time_sec=elapsed
            )
            self._update_agent_progress("advisor", "completed", 95, "Agent 7 completed", elapsed=elapsed)

            # ----------------------------------------------------
            # AGENT 8: FINAL EXECUTIVE REPORT & PDF GENERATION
            # ----------------------------------------------------
            self._update_agent_progress("report", "processing", 97, "Agent 8: Compiling final startup verdict and generating PDF...")
            t0 = time.time()
            report_agent = ReportGeneratorAgent()
            report_context = {
                "idea": StartupIdea.get_by_id(self.idea_id),
                "analysis_dict": analysis_dict
            }
            report_res = report_agent.run(report_context)
            elapsed = round(time.time() - t0, 2)
            analysis_dict["report"] = {"data": report_res}

            AnalysisResult.save_or_update(
                idea_id=self.idea_id,
                agent_name="report",
                result_data=report_res,
                execution_time_sec=elapsed
            )

            # Generate downloadable PDF
            all_comps = Competitor.get_by_idea(self.idea_id)
            updated_idea = StartupIdea.get_by_id(self.idea_id)
            pdf_filename = report_agent.generate_pdf_document(
                idea=updated_idea,
                analysis_dict=analysis_dict,
                competitors=all_comps,
                report_data=report_res
            )

            # Save report to DB
            ValidationReport.save_report(
                idea_id=self.idea_id,
                user_id=idea.get("user_id"),
                summary_text=report_res.get("executive_summary"),
                viability_score=report_res.get("viability_score", 78),
                market_score=report_res.get("market_score", 80),
                competition_score=report_res.get("competition_score", 75),
                execution_score=report_res.get("execution_score", 80),
                risk_score=report_res.get("risk_score", 35),
                pdf_filename=pdf_filename,
                full_report_data=report_res
            )

            # Update idea status to 'completed'
            final_rec = report_res.get("recommendation", "PROCEED")
            StartupIdea.update_status(
                idea_id=self.idea_id,
                status="completed",
                viability_score=report_res.get("viability_score", 78),
                recommendation=final_rec
            )
            self._update_agent_progress("report", "completed", 100, "Agent 8 completed", elapsed=elapsed)

            _ACTIVE_PIPELINES[self.idea_id].update({
                "percent": 100,
                "current_step": "completed",
                "message": f"Validation complete! Verdict: {final_rec}",
                "status": "completed",
                "pdf_filename": pdf_filename,
                "viability_score": report_res.get("viability_score", 78),
                "recommendation": final_rec
            })

            return {
                "status": "completed",
                "idea_id": self.idea_id,
                "viability_score": report_res.get("viability_score"),
                "recommendation": final_rec,
                "pdf_filename": pdf_filename
            }

        except Exception as e:
            logger.error(f"Orchestration pipeline failed for idea {self.idea_id}: {e}", exc_info=True)
            if self.idea_id in _ACTIVE_PIPELINES:
                curr = _ACTIVE_PIPELINES[self.idea_id].get("current_step", "error")
                if curr in _ACTIVE_PIPELINES[self.idea_id].get("agents", {}):
                    _ACTIVE_PIPELINES[self.idea_id]["agents"][curr]["status"] = "failed"
                _ACTIVE_PIPELINES[self.idea_id].update({
                    "percent": 100,
                    "current_step": "error",
                    "message": f"Pipeline error: {str(e)}",
                    "status": "failed"
                })
            StartupIdea.update_status(self.idea_id, "failed")
            raise e

    def run_async(self):
        """Spawns a background thread to execute the pipeline non-blockingly"""
        thread = threading.Thread(target=self.run_synchronous, daemon=True)
        thread.start()
        return thread
