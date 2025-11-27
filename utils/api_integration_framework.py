import aiohttp
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)

class APIProvider(ABC):
    """API統合のベースクラス"""
    
    def __init__(self, name: str, base_url: str, api_key: str = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.rate_limits = {}
        self.cache = {}
        self.cache_ttl = 300  # 5分のキャッシュ
    
    async def initialize(self):
        """API接続を初期化"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
    
    async def cleanup(self):
        """リソースをクリーンアップ"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self):
        """認証処理"""
        pass
    
    @abstractmethod
    async def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """API リクエストを実行"""
        pass
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """キャッシュが有効かチェック"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return (datetime.now() - cached_time).seconds < self.cache_ttl
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """キャッシュからデータを取得"""
        if self.is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        return None
    
    def set_cache(self, cache_key: str, data: Any):
        """データをキャッシュに保存"""
        self.cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }

class GitHubAPI(APIProvider):
    """GitHub API統合"""
    
    def __init__(self, api_key: str = None):
        super().__init__("GitHub", "https://api.github.com", api_key)
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if api_key:
            self.headers["Authorization"] = f"token {api_key}"
    
    async def authenticate(self):
        """GitHub認証確認"""
        if self.api_key:
            try:
                response = await self.make_request("/user")
                logger.info(f"GitHub API authenticated as: {response.get('login', 'Unknown')}")
            except Exception as e:
                logger.warning(f"GitHub authentication failed: {e}")
    
    async def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """GitHub API リクエスト"""
        url = f"{self.base_url}{endpoint}"
        
        async with self.session.request(method, url, headers=self.headers, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                raise Exception("リソースが見つかりません")
            elif response.status == 403:
                raise Exception("API制限に達しました")
            else:
                raise Exception(f"GitHub API エラー: {response.status}")
    
    async def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """ユーザーのリポジトリ一覧を取得"""
        cache_key = f"repos_{username}"
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        repos = await self.make_request(f"/users/{username}/repos")
        self.set_cache(cache_key, repos)
        return repos
    
    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """リポジトリ情報を取得"""
        cache_key = f"repo_{owner}_{repo}"
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        repo_info = await self.make_request(f"/repos/{owner}/{repo}")
        self.set_cache(cache_key, repo_info)
        return repo_info
    
    async def get_repo_commits(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """リポジトリのコミット履歴を取得"""
        params = {"per_page": limit}
        commits = await self.make_request(f"/repos/{owner}/{repo}/commits", params=params)
        return commits

class NewsAPI(APIProvider):
    """News API統合"""
    
    def __init__(self, api_key: str = None):
        super().__init__("NewsAPI", "https://newsapi.org/v2", api_key)
        self.headers = {"X-API-Key": api_key} if api_key else {}
    
    async def authenticate(self):
        """News API認証確認"""
        if not self.api_key:
            logger.warning("News API key not provided")
            return
        
        try:
            # Test request
            await self.make_request("/top-headlines", params={"country": "jp", "pageSize": 1})
            logger.info("News API authenticated successfully")
        except Exception as e:
            logger.warning(f"News API authentication failed: {e}")
    
    async def make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """News API リクエスト"""
        url = f"{self.base_url}{endpoint}"
        
        async with self.session.request(method, url, headers=self.headers, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 401:
                raise Exception("API キーが無効です")
            elif response.status == 429:
                raise Exception("API制限に達しました")
            else:
                raise Exception(f"News API エラー: {response.status}")
    
    async def get_top_headlines(self, country: str = "jp", category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """トップニュースを取得"""
        params = {"country": country, "pageSize": limit}
        if category:
            params["category"] = category
        
        cache_key = f"headlines_{country}_{category}_{limit}"
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        response = await self.make_request("/top-headlines", params=params)
        articles = response.get("articles", [])
        self.set_cache(cache_key, articles)
        return articles
    
    async def search_news(self, query: str, language: str = "ja", limit: int = 10) -> List[Dict[str, Any]]:
        """ニュースを検索"""
        params = {
            "q": query,
            "language": language,
            "pageSize": limit,
            "sortBy": "publishedAt"
        }
        
        response = await self.make_request("/everything", params=params)
        return response.get("articles", [])

class TavilyAPI(APIProvider):
    """Tavily検索API統合"""
    
    def __init__(self, api_key: str = None):
        super().__init__("Tavily", "https://api.tavily.com", api_key)
        self.headers = {"Content-Type": "application/json"}
    
    async def authenticate(self):
        """Tavily認証確認"""
        if not self.api_key:
            logger.warning("Tavily API key not provided")
    
    async def make_request(self, endpoint: str, method: str = "POST", **kwargs) -> Dict[str, Any]:
        """Tavily API リクエスト"""
        url = f"{self.base_url}{endpoint}"
        
        if "json" in kwargs:
            kwargs["json"]["api_key"] = self.api_key
        
        async with self.session.request(method, url, headers=self.headers, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Tavily API エラー: {response.status}")
    
    async def search(self, query: str, max_results: int = 5, include_domains: List[str] = None) -> List[Dict[str, Any]]:
        """Web検索を実行"""
        cache_key = f"search_{query}_{max_results}"
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": False
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        
        response = await self.make_request("/search", json=payload)
        results = response.get("results", [])
        self.set_cache(cache_key, results)
        return results

class APIIntegrationFramework:
    """API統合フレームワーク"""
    
    def __init__(self):
        self.providers = {}
        self.initialized = False
    
    async def initialize(self):
        """フレームワークを初期化"""
        if self.initialized:
            return
        
        # GitHub API
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self.providers["github"] = GitHubAPI(github_token)
        
        # News API
        news_api_key = os.environ.get("NEWS_API_KEY")
        if news_api_key:
            self.providers["news"] = NewsAPI(news_api_key)
        
        # Tavily API
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if tavily_api_key:
            self.providers["tavily"] = TavilyAPI(tavily_api_key)
        
        # すべてのプロバイダーを初期化
        for provider in self.providers.values():
            try:
                await provider.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize {provider.name}: {e}")
        
        self.initialized = True
        logger.info(f"API Integration Framework initialized with {len(self.providers)} providers")
    
    async def cleanup(self):
        """リソースをクリーンアップ"""
        for provider in self.providers.values():
            await provider.cleanup()
    
    def get_provider(self, name: str) -> Optional[APIProvider]:
        """指定されたプロバイダーを取得"""
        return self.providers.get(name)
    
    def is_available(self, provider_name: str) -> bool:
        """プロバイダーが利用可能かチェック"""
        return provider_name in self.providers
    
    async def add_custom_provider(self, provider: APIProvider):
        """カスタムプロバイダーを追加"""
        await provider.initialize()
        self.providers[provider.name.lower()] = provider
        logger.info(f"Added custom provider: {provider.name}")
    
    async def github_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """GitHub リポジトリ情報を取得"""
        if not self.is_available("github"):
            return None
        
        try:
            github = self.get_provider("github")
            return await github.get_repo_info(owner, repo)
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Web検索を実行"""
        if self.is_available("tavily"):
            try:
                tavily = self.get_provider("tavily")
                return await tavily.search(query, max_results)
            except Exception as e:
                logger.error(f"Tavily search error: {e}")
        
        return []
    
    async def get_latest_news(self, query: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """最新ニュースを取得"""
        if not self.is_available("news"):
            return []
        
        try:
            news = self.get_provider("news")
            if query:
                return await news.search_news(query, limit=limit)
            else:
                return await news.get_top_headlines(limit=limit)
        except Exception as e:
            logger.error(f"News API error: {e}")
            return []

# グローバルインスタンス
api_framework = APIIntegrationFramework()