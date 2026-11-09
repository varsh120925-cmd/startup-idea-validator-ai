import copy
import logging

logger = logging.getLogger(__name__)

class ContextStore:
    """Manages shared execution state and memory passed sequentially between AI agents"""

    def __init__(self, initial_data=None):
        self._data = initial_data or {}
        self._history = []

    def set(self, key, value):
        self._data[key] = value
        self._history.append({"action": "set", "key": key})

    def get(self, key, default=None):
        return self._data.get(key, default)

    def update(self, new_data):
        if isinstance(new_data, dict):
            self._data.update(new_data)

    def to_dict(self):
        return copy.deepcopy(self._data)

    def get_summary_context(self):
        """Returns a condensed context dictionary suitable for passing into subsequent LLM prompts"""
        return {
            "title": self._data.get("title"),
            "industry": self._data.get("industry"),
            "raw_description": self._data.get("raw_description"),
            "extractor_data": self._data.get("extractor_data", {}),
            "market_data": self._data.get("market_data", {}),
            "competitor_data": self._data.get("competitor_data", {}),
            "swot_data": self._data.get("swot_data", {}),
            "mvp_data": self._data.get("mvp_data", {}),
            "gtm_data": self._data.get("gtm_data", {})
        }
