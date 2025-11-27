"""
Adaptive Learning Engine - Real-time learning and personality adaptation system
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

class AdaptiveLearningEngine:
    """Advanced adaptive learning system for real-time personality and preference learning"""
    
    def __init__(self):
        # Learning components
        self.interaction_patterns = defaultdict(list)
        self.preference_scores = defaultdict(dict)
        self.emotional_patterns = defaultdict(deque)
        self.response_effectiveness = defaultdict(list)
        self.topic_interests = defaultdict(dict)
        self.communication_styles = defaultdict(dict)
        
        # Learning parameters
        self.max_pattern_history = 1000
        self.learning_rate = 0.1
        self.decay_factor = 0.95
        self.significance_threshold = 0.3
        
        # Advanced learning features
        self.personality_clusters = {}
        self.behavior_predictions = {}
        self.adaptation_strategies = {}
        
        logger.info("Adaptive Learning Engine initialized")
    
    async def learn_from_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from a single interaction and update user model"""
        try:
            learning_results = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'learning_updates': [],
                'insights_discovered': [],
                'adaptation_recommendations': []
            }
            
            # Extract interaction features
            features = self._extract_interaction_features(interaction_data)
            
            # Update interaction patterns
            pattern_updates = await self._update_interaction_patterns(user_id, features)
            learning_results['learning_updates'].extend(pattern_updates)
            
            # Learn communication preferences
            comm_insights = await self._learn_communication_preferences(user_id, interaction_data)
            learning_results['insights_discovered'].extend(comm_insights)
            
            # Update emotional patterns
            emotional_updates = await self._update_emotional_patterns(user_id, interaction_data)
            learning_results['learning_updates'].extend(emotional_updates)
            
            # Learn topic interests
            topic_updates = await self._learn_topic_interests(user_id, interaction_data)
            learning_results['learning_updates'].extend(topic_updates)
            
            # Generate adaptation strategies
            adaptations = await self._generate_adaptation_strategies(user_id)
            learning_results['adaptation_recommendations'] = adaptations
            
            # Update predictive models
            await self._update_predictive_models(user_id, features)
            
            return learning_results
            
        except Exception as e:
            logger.error(f"Error in adaptive learning: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'learning_updates': []
            }
    
    def _extract_interaction_features(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meaningful features from interaction"""
        features = {
            'message_length': len(interaction_data.get('user_message', '')),
            'response_time': interaction_data.get('response_time', 0),
            'question_type': self._classify_question_type(interaction_data.get('user_message', '')),
            'emotional_tone': interaction_data.get('emotional_tone', 'neutral'),
            'complexity_level': self._analyze_complexity_level(interaction_data.get('user_message', '')),
            'topics_mentioned': self._extract_topics(interaction_data.get('user_message', '')),
            'interaction_context': interaction_data.get('context', ''),
            'user_satisfaction_indicators': self._detect_satisfaction_signals(interaction_data)
        }
        
        return features
    
    def _classify_question_type(self, message: str) -> str:
        """Classify the type of question/message"""
        message_lower = message.lower()
        
        # 質問タイプの分類
        if any(word in message_lower for word in ['なぜ', 'どうして', 'why', 'how']):
            return 'explanation_seeking'
        elif any(word in message_lower for word in ['どこ', 'いつ', 'where', 'when']):
            return 'factual_inquiry'
        elif any(word in message_lower for word in ['どう思う', 'どう考える', 'opinion']):
            return 'opinion_seeking'
        elif any(word in message_lower for word in ['助けて', 'help', 'サポート']):
            return 'help_request'
        elif any(word in message_lower for word in ['作って', 'create', '生成']):
            return 'creation_request'
        elif '?' in message or '？' in message:
            return 'general_question'
        else:
            return 'statement'
    
    def _analyze_complexity_level(self, message: str) -> str:
        """Analyze message complexity level"""
        word_count = len(message.split())
        sentence_count = len([s for s in message.split('.') if s.strip()])
        
        # 複雑さの指標
        technical_terms = sum(1 for word in message.split() 
                            if len(word) > 8 or any(char in word for char in ['技術', 'システム', 'アルゴリズム']))
        
        if word_count > 50 or technical_terms > 2:
            return 'high'
        elif word_count > 20 or technical_terms > 0:
            return 'medium'
        else:
            return 'low'
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract main topics from message"""
        topics = []
        message_lower = message.lower()
        
        # トピック辞書
        topic_keywords = {
            'technology': ['ai', '人工知能', 'プログラミング', 'コンピュータ', 'ソフトウェア'],
            'science': ['科学', '研究', '実験', '理論', '発見'],
            'entertainment': ['映画', '音楽', 'ゲーム', '本', '小説'],
            'daily_life': ['仕事', '学校', '家族', '友達', '日常'],
            'health': ['健康', '運動', '食事', '病気', '医療'],
            'travel': ['旅行', '観光', '国', '文化', '言語']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_satisfaction_signals(self, interaction_data: Dict[str, Any]) -> Dict[str, float]:
        """Detect user satisfaction signals"""
        signals = {
            'positive_feedback': 0.0,
            'engagement_level': 0.0,
            'follow_up_likelihood': 0.0
        }
        
        user_message = interaction_data.get('user_message', '').lower()
        ai_response = interaction_data.get('ai_response', '')
        
        # ポジティブなフィードバックの検出
        positive_indicators = ['ありがとう', 'thanks', '助かる', '素晴らしい', 'いいね', 'good']
        negative_indicators = ['わからない', 'confused', '違う', 'wrong', '間違い']
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in user_message)
        negative_count = sum(1 for indicator in negative_indicators if indicator in user_message)
        
        signals['positive_feedback'] = max(0, min(1, (positive_count - negative_count) / 3))
        
        # エンゲージメントレベル
        message_length = len(user_message)
        if message_length > 100:
            signals['engagement_level'] = 0.8
        elif message_length > 50:
            signals['engagement_level'] = 0.6
        else:
            signals['engagement_level'] = 0.4
        
        # フォローアップの可能性
        question_markers = ['?', '？', 'もっと', 'さらに', 'more', 'また']
        if any(marker in user_message for marker in question_markers):
            signals['follow_up_likelihood'] = 0.7
        else:
            signals['follow_up_likelihood'] = 0.3
        
        return signals
    
    async def _update_interaction_patterns(self, user_id: int, features: Dict[str, Any]) -> List[str]:
        """Update interaction patterns for user"""
        updates = []
        
        # パターンの記録
        pattern_key = f"{features['question_type']}_{features['complexity_level']}"
        self.interaction_patterns[user_id].append({
            'pattern': pattern_key,
            'timestamp': datetime.now(),
            'features': features
        })
        
        # 履歴の制限
        if len(self.interaction_patterns[user_id]) > self.max_pattern_history:
            self.interaction_patterns[user_id] = self.interaction_patterns[user_id][-self.max_pattern_history:]
        
        # パターン分析
        recent_patterns = [p['pattern'] for p in self.interaction_patterns[user_id][-10:]]
        pattern_frequency = {}
        for pattern in recent_patterns:
            pattern_frequency[pattern] = pattern_frequency.get(pattern, 0) + 1
        
        # 主要パターンの特定
        if pattern_frequency:
            most_common_pattern = max(pattern_frequency, key=pattern_frequency.get)
            updates.append(f"主要な交流パターン: {most_common_pattern}")
        
        return updates
    
    async def _learn_communication_preferences(self, user_id: int, interaction_data: Dict[str, Any]) -> List[str]:
        """Learn user's communication preferences"""
        insights = []
        
        user_message = interaction_data.get('user_message', '')
        
        # 丁寧語の使用傾向
        polite_indicators = ['です', 'ます', 'ください', 'ありがとうございます']
        casual_indicators = ['だよ', 'だね', 'じゃん', 'ってか']
        
        polite_score = sum(1 for indicator in polite_indicators if indicator in user_message)
        casual_score = sum(1 for indicator in casual_indicators if indicator in user_message)
        
        if polite_score > casual_score:
            self.communication_styles[user_id]['formality'] = 'polite'
            insights.append("丁寧な表現を好む傾向")
        elif casual_score > polite_score:
            self.communication_styles[user_id]['formality'] = 'casual'
            insights.append("カジュアルな表現を好む傾向")
        
        # 詳細レベルの好み
        if len(user_message.split()) > 30:
            self.communication_styles[user_id]['detail_preference'] = 'detailed'
            insights.append("詳細な説明を好む傾向")
        else:
            self.communication_styles[user_id]['detail_preference'] = 'concise'
            insights.append("簡潔な説明を好む傾向")
        
        return insights
    
    async def _update_emotional_patterns(self, user_id: int, interaction_data: Dict[str, Any]) -> List[str]:
        """Update emotional patterns for user"""
        updates = []
        
        emotional_tone = interaction_data.get('emotional_tone', 'neutral')
        timestamp = datetime.now()
        
        # 感情パターンの記録
        self.emotional_patterns[user_id].append({
            'emotion': emotional_tone,
            'timestamp': timestamp,
            'context': interaction_data.get('context', '')
        })
        
        # 履歴の制限（最近30件）
        if len(self.emotional_patterns[user_id]) > 30:
            self.emotional_patterns[user_id].popleft()
        
        # 感情トレンドの分析
        recent_emotions = [p['emotion'] for p in list(self.emotional_patterns[user_id])[-10:]]
        if len(recent_emotions) >= 3:
            emotion_counts = {}
            for emotion in recent_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            dominant_emotion = max(emotion_counts, key=emotion_counts.get)
            updates.append(f"最近の感情傾向: {dominant_emotion}")
        
        return updates
    
    async def _learn_topic_interests(self, user_id: int, interaction_data: Dict[str, Any]) -> List[str]:
        """Learn user's topic interests"""
        updates = []
        
        user_message = interaction_data.get('user_message', '')
        topics = self._extract_topics(user_message)
        
        # トピック興味度の更新
        for topic in topics:
            if topic not in self.topic_interests[user_id]:
                self.topic_interests[user_id][topic] = 0.0
            
            # 興味度の増加
            self.topic_interests[user_id][topic] += self.learning_rate
            updates.append(f"'{topic}'への興味度が増加")
        
        # 興味度の減衰（他のトピック）
        for topic in self.topic_interests[user_id]:
            if topic not in topics:
                self.topic_interests[user_id][topic] *= self.decay_factor
        
        return updates
    
    async def _generate_adaptation_strategies(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized adaptation strategies"""
        strategies = []
        
        # コミュニケーションスタイルの適応
        comm_style = self.communication_styles.get(user_id, {})
        if comm_style.get('formality') == 'polite':
            strategies.append({
                'type': 'communication',
                'strategy': 'formal_tone',
                'description': '丁寧語を使用した応答'
            })
        elif comm_style.get('formality') == 'casual':
            strategies.append({
                'type': 'communication',
                'strategy': 'casual_tone',
                'description': 'フレンドリーで親しみやすい応答'
            })
        
        # 興味トピックの活用
        topic_interests = self.topic_interests.get(user_id, {})
        if topic_interests:
            top_topic = max(topic_interests, key=topic_interests.get)
            if topic_interests[top_topic] > 0.5:
                strategies.append({
                    'type': 'content',
                    'strategy': 'topic_focus',
                    'description': f'{top_topic}関連の内容を優先'
                })
        
        # 感情パターンに基づく適応
        if user_id in self.emotional_patterns:
            recent_emotions = [p['emotion'] for p in list(self.emotional_patterns[user_id])[-5:]]
            if len(recent_emotions) >= 3:
                if 'positive' in recent_emotions[-3:]:
                    strategies.append({
                        'type': 'emotional',
                        'strategy': 'maintain_positivity',
                        'description': 'ポジティブなトーンを維持'
                    })
                elif 'negative' in recent_emotions[-3:]:
                    strategies.append({
                        'type': 'emotional',
                        'strategy': 'supportive_approach',
                        'description': 'サポーティブで励ましのアプローチ'
                    })
        
        return strategies
    
    async def _update_predictive_models(self, user_id: int, features: Dict[str, Any]):
        """Update predictive models for user behavior"""
        try:
            # 次の質問タイプの予測
            recent_patterns = [p['features']['question_type'] 
                             for p in self.interaction_patterns[user_id][-5:]]
            
            if len(recent_patterns) >= 3:
                # 簡単な予測モデル（最頻値）
                pattern_counts = {}
                for pattern in recent_patterns:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                
                predicted_next = max(pattern_counts, key=pattern_counts.get)
                self.behavior_predictions[user_id] = {
                    'next_question_type': predicted_next,
                    'confidence': pattern_counts[predicted_next] / len(recent_patterns),
                    'updated': datetime.now()
                }
        
        except Exception as e:
            logger.debug(f"Error updating predictive models: {e}")
    
    def get_user_profile_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user profile summary"""
        profile = {
            'user_id': user_id,
            'interaction_count': len(self.interaction_patterns.get(user_id, [])),
            'communication_style': self.communication_styles.get(user_id, {}),
            'topic_interests': dict(sorted(
                self.topic_interests.get(user_id, {}).items(),
                key=lambda x: x[1], reverse=True
            )[:5]),  # Top 5 interests
            'emotional_patterns': self._analyze_emotional_patterns(user_id),
            'behavior_predictions': self.behavior_predictions.get(user_id, {}),
            'adaptation_strategies': []
        }
        
        return profile
    
    def _analyze_emotional_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze emotional patterns for user"""
        if user_id not in self.emotional_patterns:
            return {}
        
        emotions = [p['emotion'] for p in self.emotional_patterns[user_id]]
        if not emotions:
            return {}
        
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get),
            'emotion_distribution': emotion_counts,
            'recent_trend': emotions[-3:] if len(emotions) >= 3 else emotions
        }
    
    async def predict_user_needs(self, user_id: int, current_context: str = "") -> Dict[str, Any]:
        """Predict user needs based on learning patterns"""
        try:
            predictions = {
                'user_id': user_id,
                'predicted_needs': [],
                'confidence_scores': {},
                'recommendations': []
            }
            
            # 興味トピックに基づく予測
            topic_interests = self.topic_interests.get(user_id, {})
            if topic_interests:
                top_topics = sorted(topic_interests.items(), key=lambda x: x[1], reverse=True)[:3]
                for topic, interest_score in top_topics:
                    if interest_score > 0.3:
                        predictions['predicted_needs'].append(f"{topic}関連の情報や話題")
                        predictions['confidence_scores'][topic] = interest_score
            
            # 行動パターンに基づく予測
            behavior_pred = self.behavior_predictions.get(user_id, {})
            if behavior_pred and behavior_pred.get('confidence', 0) > 0.5:
                next_type = behavior_pred['next_question_type']
                predictions['predicted_needs'].append(f"{next_type}タイプの質問への対応")
                predictions['confidence_scores']['behavior'] = behavior_pred['confidence']
            
            # 推奨事項の生成
            if predictions['predicted_needs']:
                predictions['recommendations'] = [
                    "ユーザーの興味に合わせた話題の提案",
                    "予測される質問タイプに適した応答準備",
                    "過去のポジティブな反応を参考にした対話スタイルの継続"
                ]
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting user needs: {e}")
            return {'user_id': user_id, 'error': str(e)}

# Global instance
adaptive_learning_engine = AdaptiveLearningEngine()