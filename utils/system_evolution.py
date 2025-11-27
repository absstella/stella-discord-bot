"""
System-Level Evolution Components
STELLAのシステムレベルの自己進化機能（パフォーマンス、設定、コード、機能）
"""

import logging
import json
import os
import asyncio
import psutil
import time
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """パフォーマンスの監視と最適化"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.target_response_time = config.get('target_response_time_ms', 500)
        self.memory_threshold = config.get('memory_threshold_mb', 512)
        self.history = []
    
    async def monitor_performance(self) -> Dict[str, Any]:
        """現在のパフォーマンスを測定"""
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent(interval=0.1)
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'memory_mb': memory_usage,
            'cpu_percent': cpu_percent
        }
        
        self.history.append(metrics)
        if len(self.history) > 100:
            self.history.pop(0)
            
        return metrics
    
    async def optimize(self) -> List[str]:
        """必要に応じて最適化を実行"""
        actions = []
        metrics = await self.monitor_performance()
        
        # メモリ最適化
        if metrics['memory_mb'] > self.memory_threshold:
            import gc
            gc.collect()
            actions.append(f"Garbage collection triggered (Memory: {metrics['memory_mb']:.1f}MB)")
            
        return actions

class ConfigurationEvolver:
    """設定の自動進化"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.adaptation_rate = config.get('adaptation_rate', 0.1)
    
    async def evaluate_configuration(self, feedback_data: Dict) -> List[str]:
        """現在の設定を評価し、必要なら調整"""
        changes = []
        # ここにA/Bテストの結果分析やパラメータ調整ロジックを実装
        # 現段階ではプレースホルダー
        return changes

class CodeAnalyzer:
    """コード品質の分析"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    async def analyze_codebase(self) -> List[Dict]:
        """コードベースを分析して改善点を提案"""
        suggestions = []
        # ここに静的解析やパターンマッチングによる改善提案ロジックを実装
        return suggestions

class SystemHealthMonitor:
    """システム健全性の監視"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.errors = []
    
    def log_error(self, error_type: str, message: str):
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message
        })
    
    def get_health_report(self) -> Dict:
        uptime = datetime.now() - self.start_time
        return {
            'uptime_seconds': uptime.total_seconds(),
            'error_count': len(self.errors),
            'status': 'healthy' if len(self.errors) < 10 else 'degraded'
        }

class FeatureEvolver:
    """機能の自動進化と提案"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.feature_usage = {}
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
    
    def record_usage(self, feature_name: str):
        """機能の使用を記録"""
        if feature_name not in self.feature_usage:
            self.feature_usage[feature_name] = 0
        self.feature_usage[feature_name] += 1
    
    async def analyze_feature_usage(self) -> List[str]:
        """機能の使用状況を分析"""
        suggestions = []
        # 使用頻度の低い機能や高い機能に基づく提案
        sorted_features = sorted(self.feature_usage.items(), key=lambda x: x[1], reverse=True)
        if sorted_features:
            top_feature = sorted_features[0]
            suggestions.append(f"Feature '{top_feature[0]}' is highly used ({top_feature[1]} times). Consider enhancing it.")
            
        return suggestions

    async def propose_new_features(self, conversation_logs: List[Dict]) -> List[Dict]:
        """会話ログから新機能を提案"""
        if not self.model or not conversation_logs:
            return []
            
        # 最近の会話テキストを抽出
        recent_conversations = "\n".join([
            f"{log.get('author', 'User')}: {log.get('content', '')}" 
            for log in conversation_logs[-50:] # 最新50件
        ])
        
        prompt = f"""
        以下のDiscordチャットログを分析し、ユーザーが求めている可能性のある「Botの新機能」を1つ提案してください。
        
        会話ログ:
        {recent_conversations}
        
        条件:
        1. ユーザーが明示的に求めていなくても、文脈から「あると便利そう」な機能を推測すること。
        2. 既存の機能（会話、サイコロなど）と重複しないこと。
        3. 実装可能であること（Discord Botとして）。
        
        出力形式（JSON）:
        {{
            "feature_name": "機能名（英語_スネークケース）",
            "title": "機能名（日本語）",
            "description": "機能の説明と、なぜこれが必要だと思ったかの理由",
            "command_idea": "!command_name",
            "confidence": 0.0〜1.0（確信度）
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text
            # JSON抽出
            import re
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            json_str = match.group(1) if match else text
            proposal = json.loads(json_str)
            
            if proposal.get("confidence", 0) > 0.7:
                return [proposal]
            return []
            
        except Exception as e:
            logger.error(f"Error proposing features: {e}")
            return []

class SystemEvolutionManager:
    """システム進化全体を管理するマネージャー"""
    
    def __init__(self, config_path: str = "config/evolution_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        sys_config = self.config.get('system_evolution', {})
        
        self.optimizer = PerformanceOptimizer(sys_config.get('performance_optimization', {}))
        self.config_evolver = ConfigurationEvolver(sys_config.get('configuration_evolution', {}))
        self.code_analyzer = CodeAnalyzer(sys_config.get('code_analysis', {}))
        self.health_monitor = SystemHealthMonitor()
        self.feature_evolver = FeatureEvolver(sys_config.get('feature_development', {}))
        
        # ログディレクトリの準備
        self.log_dir = self.config.get('logging', {}).get('log_directory', 'data/evolution_logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
    def _load_config(self) -> Dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load evolution config: {e}")
            return {}

    async def run_maintenance_cycle(self):
        """定期メンテナンスサイクルの実行"""
        logger.info("Starting system evolution maintenance cycle")
        
        # パフォーマンス最適化
        if self.config.get('system_evolution', {}).get('performance_optimization', {}).get('enabled'):
            actions = await self.optimizer.optimize()
            for action in actions:
                logger.info(f"Optimization action: {action}")
                self._log_system_change("performance_optimization", action)
        
        # 機能使用状況の分析
        if self.config.get('system_evolution', {}).get('feature_development', {}).get('enabled'):
            suggestions = await self.feature_evolver.analyze_feature_usage()
            for suggestion in suggestions:
                logger.info(f"Feature suggestion: {suggestion}")
        
        # 設定の保存（もし変更があれば）
        # self._save_config()
        
    def _log_system_change(self, change_type: str, description: str):
        """システム変更をログに記録"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"system_changes_{today}.json")
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': change_type,
            'description': description
        }
        
        entries = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            except:
                pass
        
        entries.append(entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
