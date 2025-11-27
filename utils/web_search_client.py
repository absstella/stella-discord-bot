"""
Web Search Client
Uses duckduckgo-search to perform web searches and extract information
"""

import logging
import asyncio
from typing import List, Dict, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebSearchClient:
    def __init__(self):
        self.ddgs = DDGS()

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Perform a web search and return results"""
        # DDGS is synchronous, so run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_sync, query, num_results)

    def _search_sync(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Synchronous search implementation"""
        results = []
        try:
            # Use text search
            ddg_results = self.ddgs.text(query, max_results=num_results)
            
            if ddg_results:
                for r in ddg_results:
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
                    
        except Exception as e:
            logger.error(f"WebSearchClient: Search error: {e}")
            
        return results

    def close(self):
        """Clean up resources"""
        pass
