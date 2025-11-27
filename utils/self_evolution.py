"""
Self-Evolution Core System
STELLAの自己進化機能のコアコンポーネント
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)


class ConversationAnalyzer:
    """会話から情報を自動抽出するアナライザー"""
    
    def __init__(self):
        self.interest_keywords = {
            'ゲーム': ['ゲーム', 'プレイ', 'マイクラ', 'minecraft', 'valorant', 'apex', 'fps'],
            '音楽': ['音楽', '曲', '歌', 'ライブ', 'コンサート', 'バンド'],
            'アニメ': ['アニメ', '漫画', 'マンガ', 'アニメーション'],
            'プログラミング': ['コード', 'プログラム', '開発', 'python', 'javascript', 'ai'],
            '旅行': ['旅行', '旅', '観光', '海外', '国内旅行'],
        }
        
        self.personality_patterns = {
            '友好的': ['ありがとう', 'うれしい', '楽しい', '面白い'],
            '技術志向': ['技術', 'システム', 'コード', '実装', '開発'],
            '好奇心旺盛': ['知りたい', '教えて', 'どうやって', 'なぜ', '興味'],
            '几帳面': ['整理', '管理', '記録', 'ちゃんと', 'きちんと'],
        }
    
    async def analyze_conversation(self, message: str, user_id: int) -> Dict[str, Any]:
        """
        会話を分析して情報を抽出
        
        Returns:
            {
                'interests': List[str],
                'personality_traits': List[str],
                'emotions': List[str],
                'topics': List[str],
                'confidence': float
            }
        """
        result = {
            'interests': [],
            'personality_traits': [],
            'emotions': [],
            'topics': [],
            'confidence': 0.0
        }
        
        message_lower = message.lower()
        
        # 興味の検出
        for interest, keywords in self.interest_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                result['interests'].append(interest)
        
        # 性格特性の検出
        for trait, patterns in self.personality_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                result['personality_traits'].append(trait)
        
        # 感情の検出
        emotions = self._detect_emotions(message)
        result['emotions'] = emotions
        
        # トピックの抽出
        topics = self._extract_topics(message)
        result['topics'] = topics
        
        # 信頼度スコアの計算
        result['confidence'] = self._calculate_confidence(result)
        
        return result
    
    def _detect_emotions(self, message: str) -> List[str]:
        """感情を検出"""
        emotions = []
        emotion_patterns = {
            '喜び': ['嬉しい', 'うれしい', '楽しい', '最高', 'やった'],
            '悲しみ': ['悲しい', 'つらい', '残念', '寂しい'],
            '怒り': ['怒', 'むかつく', 'イライラ'],
            '驚き': ['驚', 'びっくり', 'すごい', 'まじで'],
            '期待': ['楽しみ', '期待', 'わくわく'],
        }
        
        message_lower = message.lower()
        for emotion, patterns in emotion_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                emotions.append(emotion)
        
        return emotions
    
    def _extract_topics(self, message: str) -> List[str]:
        """トピックを抽出"""
        # 簡易的なトピック抽出（名詞を中心に）
        topics = []
        
        # よく使われるトピックキーワード
        topic_keywords = [
            'ゲーム', '音楽', 'アニメ', '映画', '本', '料理',
            '旅行', 'スポーツ', '仕事', '勉強', '趣味'
        ]
        
        for keyword in topic_keywords:
            if keyword in message:
                topics.append(keyword)
        
        return topics
    
    def _calculate_confidence(self, result: Dict) -> float:
        """信頼度スコアを計算"""
        score = 0.0
        
        # 検出された要素の数に基づいてスコアを計算
        if result['interests']:
            score += 0.3
        if result['personality_traits']:
            score += 0.3
        if result['emotions']:
            score += 0.2
        if result['topics']:
            score += 0.2
        
        return min(score, 1.0)


class ProfileEnricher:
    """プロファイルを自動的に充実させる"""
    
    def __init__(self):
        self.min_confidence = 0.5
    
    async def enrich_profile(self, profile, analysis_result: Dict) -> Dict[str, List[str]]:
        """
        分析結果をプロファイルに統合
        
        Returns:
            Dict of changes made
        """
        changes = {
            'interests_added': [],
            'traits_added': [],
            'topics_added': []
        }
        
        # 信頼度が低い場合はスキップ
        if analysis_result['confidence'] < self.min_confidence:
            return changes
        
        # 興味を追加
        if not hasattr(profile, 'interests'):
            profile.interests = []
        
        for interest in analysis_result['interests']:
            if interest not in profile.interests:
                profile.interests.append(interest)
                changes['interests_added'].append(interest)
                logger.info(f"Added interest: {interest}")
        
        # 性格特性を追加
        if not hasattr(profile, 'personality_traits'):
            profile.personality_traits = []
        
        for trait in analysis_result['personality_traits']:
            if trait not in profile.personality_traits:
                profile.personality_traits.append(trait)
                changes['traits_added'].append(trait)
                logger.info(f"Added personality trait: {trait}")
        
        # トピックを記録（カスタム属性として）
        if not hasattr(profile, 'custom_attributes'):
            profile.custom_attributes = {}
        
        if 'discussed_topics' not in profile.custom_attributes:
            profile.custom_attributes['discussed_topics'] = []
        
        for topic in analysis_result['topics']:
            if topic not in profile.custom_attributes['discussed_topics']:
                profile.custom_attributes['discussed_topics'].append(topic)
                changes['topics_added'].append(topic)
        
        return changes


class EvolutionLogger:
    """進化イベントをログに記録"""
    
    def __init__(self, log_dir: str = "data/evolution_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def log_learning_event(self, event_type: str, user_id: int, details: Dict):
        """学習イベントを記録"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"learning_events_{today}.json")
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details
        }
        
        # ログファイルに追記
        events = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            except:
                events = []
        
        events.append(event)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Logged learning event: {event_type} for user {user_id}")
    
    def log_profile_update(self, user_id: int, changes: Dict):
        """プロファイル更新を記録"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"profile_updates_{today}.json")
        
        update = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'changes': changes
        }
        
        updates = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    updates = json.load(f)
            except:
                updates = []
        
        updates.append(update)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(updates, f, ensure_ascii=False, indent=2)
    
    def get_learning_stats(self, days: int = 7) -> Dict:
        """学習統計を取得"""
        stats = {
            'total_events': 0,
            'events_by_type': {},
            'users_learned': set()
        }
        
        # 過去N日分のログを集計
        for i in range(days):
            date = datetime.now().date()
            # 簡易実装: 今日のログのみ
            log_file = os.path.join(self.log_dir, f"learning_events_{date}.json")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        events = json.load(f)
                        stats['total_events'] += len(events)
                        
                        for event in events:
                            event_type = event.get('event_type', 'unknown')
                            stats['events_by_type'][event_type] = stats['events_by_type'].get(event_type, 0) + 1
                            stats['users_learned'].add(event.get('user_id'))
                except:
                    pass
        
        stats['users_learned'] = len(stats['users_learned'])
        return stats
