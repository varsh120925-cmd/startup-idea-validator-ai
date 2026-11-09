import time
import logging
from services.groq_service import GroqService
from services.search_service import SearchService

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all startup validator AI agents"""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.groq_service = GroqService()
        self.search_service = SearchService()

    def run(self, context):
        """
        Executes the agent lifecycle with timing, LLM call, and graceful fallback.
        Returns a dict containing agent results and metadata.
        """
        start_time = time.time()
        logger.info(f"Starting execution of agent: {self.name}")

        try:
            if self.groq_service.is_available():
                result_data = self._execute_llm(context)
                source_badge = "Live Groq LLM Inference"
            else:
                result_data = self._execute_fallback(context)
                source_badge = "Simulated Analytical Engine (Demo Mode)"

            elapsed = round(time.time() - start_time, 2)
            result_data["_meta"] = {
                "agent_name": self.name,
                "execution_time_sec": elapsed,
                "source": source_badge,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.info(f"Agent {self.name} completed in {elapsed}s")
            return result_data

        except Exception as e:
            logger.error(f"Agent {self.name} failed with LLM: {e}. Executing fallback reasoning.")
            elapsed = round(time.time() - start_time, 2)
            fallback_data = self._execute_fallback(context)
            fallback_data["_meta"] = {
                "agent_name": self.name,
                "execution_time_sec": elapsed,
                "source": f"Fallback Analytical Engine (Handled: {str(e)[:60]})",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            return fallback_data

    def _execute_llm(self, context):
        """Must be implemented by subclasses to interact with GroqService"""
        raise NotImplementedError

    def _execute_fallback(self, context):
        """Must be implemented by subclasses to provide high quality fallback when LLM is offline"""
        raise NotImplementedError
