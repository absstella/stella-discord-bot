"""
Basic conversation analysis utilities for STELLA Bot
Provides simplified analysis when advanced systems are not available
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BasicMemoryProcessor:
    """
    Basic memory processing system for conversation analysis
    """
    
    def __init__(self):
        self.conversation_memory = {}
        self.user_patterns = {}
        logger.info("Basic Memory Processor initialized")
    
    async def process_conversation(self, user_id: int, message: str, response: str, 
                                 context: Dict = None) -> Dict[str, Any]:
        """
        Process conversation with basic analysis
        """
        try:
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'basic_analysis': {
                    'message_length': len(message),
                    'response_length': len(response),
                    'language': self._detect_language(message),
                    'topics': self._extract_basic_topics(message),
                    'sentiment': self._basic_sentiment_analysis(message),
                    'question_count': message.count('?') + message.count('？'),
                    'exclamation_count': message.count('!') + message.count('！'),
                    'mentions': self._extract_mentions(message),
                    'conversation_type': self._determine_conversation_type(message)
                }
            }
            
            # Store in basic memory
            await self._store_basic_memory(user_id, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in basic conversation processing: {e}")
            return {}
    
    def _detect_language(self, text: str) -> str:
        """Basic language detection"""
        # Check for Japanese characters
        if re.search(r'[ひらがなカタカナ漢字]', text):
            return 'japanese'
        elif re.search(r'[a-zA-Z]', text):
            return 'english'
        else:
            return 'unknown'
    
    def _extract_basic_topics(self, text: str) -> List[str]:
        """Extract basic topics from text"""
        topics = []
        
        topic_keywords = {
            'technology': ['tech', 'computer', 'AI', 'robot', 'software', 'プログラミング', 'コンピュータ', 'AI', 'ロボット'],
            'entertainment': ['movie', 'game', 'music', 'anime', '映画', 'ゲーム', '音楽', 'アニメ'],
            'food': ['food', 'restaurant', 'cook', '食べ物', 'レストラン', '料理', '食事'],
            'work': ['work', 'job', 'career', '仕事', '会社', '職場'],
            'study': ['study', 'learn', 'school', '勉強', '学校', '大学'],
            'health': ['health', 'exercise', '健康', '運動'],
            'travel': ['travel', 'trip', '旅行', '観光']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _basic_sentiment_analysis(self, text: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['good', 'great', 'happy', 'love', 'excellent', '良い', '素晴らしい', '嬉しい', '好き', '最高']
        negative_words = ['bad', 'sad', 'hate', 'terrible', 'awful', '悪い', '悲しい', '嫌い', '最悪', 'つらい']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        mentions = re.findall(r'<@!?(\d+)>', text)
        return mentions
    
    def _determine_conversation_type(self, text: str) -> str:
        """Determine basic conversation type"""
        if '?' in text or '？' in text:
            return 'question'
        elif any(word in text.lower() for word in ['help', 'ヘルプ', '助けて', '教えて']):
            return 'help_request'
        elif any(word in text.lower() for word in ['thank', 'ありがとう', '感謝']):
            return 'gratitude'
        elif len(text.split()) > 20:
            return 'detailed_discussion'
        else:
            return 'casual_chat'
    
    async def _store_basic_memory(self, user_id: int, analysis: Dict[str, Any]):
        """Store basic memory"""
        try:
            if user_id not in self.conversation_memory:
                self.conversation_memory[user_id] = []
            
            self.conversation_memory[user_id].append(analysis)
            
            # Keep only last 100 conversations
            if len(self.conversation_memory[user_id]) > 100:
                self.conversation_memory[user_id] = self.conversation_memory[user_id][-50:]
            
            # Update user patterns
            self._update_user_patterns(user_id, analysis)
            
        except Exception as e:
            logger.error(f"Error storing basic memory: {e}")
    
    def _update_user_patterns(self, user_id: int, analysis: Dict[str, Any]):
        """Update user patterns based on analysis"""
        try:
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {
                    'preferred_language': 'unknown',
                    'common_topics': {},
                    'conversation_style': 'casual',
                    'sentiment_trend': [],
                    'activity_pattern': []
                }
            
            patterns = self.user_patterns[user_id]
            basic_analysis = analysis.get('basic_analysis', {})
            
            # Update language preference
            language = basic_analysis.get('language', 'unknown')
            if language != 'unknown':
                patterns['preferred_language'] = language
            
            # Update topic frequency
            topics = basic_analysis.get('topics', [])
            for topic in topics:
                patterns['common_topics'][topic] = patterns['common_topics'].get(topic, 0) + 1
            
            # Update sentiment trend
            sentiment = basic_analysis.get('sentiment', 'neutral')
            patterns['sentiment_trend'].append(sentiment)
            if len(patterns['sentiment_trend']) > 10:
                patterns['sentiment_trend'] = patterns['sentiment_trend'][-10:]
            
            # Update activity pattern
            patterns['activity_pattern'].append({
                'timestamp': analysis['timestamp'],
                'message_length': basic_analysis.get('message_length', 0),
                'conversation_type': basic_analysis.get('conversation_type', 'casual_chat')
            })
            if len(patterns['activity_pattern']) > 20:
                patterns['activity_pattern'] = patterns['activity_pattern'][-20:]
            
        except Exception as e:
            logger.error(f"Error updating user patterns: {e}")
    
    async def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Get basic user insights"""
        try:
            if user_id not in self.user_patterns:
                return {}
            
            patterns = self.user_patterns[user_id]
            recent_conversations = self.conversation_memory.get(user_id, [])[-10:]
            
            insights = {
                'basic_insights': {
                    'preferred_language': patterns.get('preferred_language', 'unknown'),
                    'conversation_count': len(self.conversation_memory.get(user_id, [])),
                    'most_common_topics': sorted(
                        patterns.get('common_topics', {}).items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:3],
                    'recent_sentiment': patterns.get('sentiment_trend', ['neutral'])[-1],
                    'conversation_style': self._assess_conversation_style(patterns),
                    'engagement_level': self._calculate_basic_engagement(recent_conversations),
                    'activity_summary': self._summarize_activity(patterns.get('activity_pattern', []))
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting user insights: {e}")
            return {}
    
    def _assess_conversation_style(self, patterns: Dict) -> str:
        """Assess conversation style from patterns"""
        activity = patterns.get('activity_pattern', [])
        if not activity:
            return 'unknown'
        
        avg_length = sum(a.get('message_length', 0) for a in activity) / len(activity)
        conversation_types = [a.get('conversation_type', 'casual_chat') for a in activity]
        
        if avg_length > 100:
            return 'detailed'
        elif conversation_types.count('question') > len(conversation_types) * 0.3:
            return 'inquisitive'
        elif conversation_types.count('help_request') > len(conversation_types) * 0.2:
            return 'help_seeking'
        else:
            return 'casual'
    
    def _calculate_basic_engagement(self, recent_conversations: List[Dict]) -> float:
        """Calculate basic engagement level"""
        if not recent_conversations:
            return 0.5
        
        engagement_factors = []
        for conv in recent_conversations:
            basic = conv.get('basic_analysis', {})
            
            # Message length factor
            length_factor = min(basic.get('message_length', 0) / 50.0, 1.0)
            
            # Question factor
            question_factor = min(basic.get('question_count', 0) / 2.0, 1.0)
            
            # Exclamation factor
            exclamation_factor = min(basic.get('exclamation_count', 0) / 2.0, 1.0)
            
            conv_engagement = (length_factor + question_factor + exclamation_factor) / 3.0
            engagement_factors.append(conv_engagement)
        
        return sum(engagement_factors) / len(engagement_factors)
    
    def _summarize_activity(self, activity_pattern: List[Dict]) -> Dict[str, Any]:
        """Summarize user activity patterns"""
        if not activity_pattern:
            return {}
        
        conversation_types = [a.get('conversation_type', 'casual_chat') for a in activity_pattern]
        avg_message_length = sum(a.get('message_length', 0) for a in activity_pattern) / len(activity_pattern)
        
        return {
            'total_interactions': len(activity_pattern),
            'average_message_length': round(avg_message_length, 1),
            'most_common_conversation_type': max(set(conversation_types), key=conversation_types.count),
            'conversation_type_distribution': {
                conv_type: conversation_types.count(conv_type)
                for conv_type in set(conversation_types)
            }
        }

class BasicConversationIntelligence:
    """
    Basic conversation intelligence for when advanced systems are not available
    """
    
    def __init__(self):
        self.memory_processor = BasicMemoryProcessor()
        self.conversation_states = {}
        logger.info("Basic Conversation Intelligence initialized")
    
    async def process_conversation_turn(self, user_id: int, guild_id: int, 
                                      message: str, context: Dict = None) -> Dict[str, Any]:
        """Process conversation turn with basic intelligence"""
        try:
            # Process with basic memory
            memory_analysis = await self.memory_processor.process_conversation(
                user_id, message, "", context
            )
            
            # Generate basic response strategy
            response_strategy = self._generate_basic_strategy(memory_analysis, context)
            
            # Track conversation state
            conv_id = f"{guild_id}_{user_id}"
            self._update_conversation_state(conv_id, memory_analysis)
            
            return {
                'conversation_id': conv_id,
                'timestamp': datetime.now().isoformat(),
                'memory_analysis': memory_analysis,
                'response_strategy': response_strategy,
                'conversation_state': self.conversation_states.get(conv_id, {}),
                'user_insights': await self.memory_processor.get_user_insights(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error in basic conversation processing: {e}")
            return {}
    
    def _generate_basic_strategy(self, analysis: Dict, context: Dict = None) -> Dict[str, Any]:
        """Generate basic response strategy"""
        basic_analysis = analysis.get('basic_analysis', {})
        
        strategy = {
            'response_approach': 'balanced',
            'emotional_tone': 'neutral',
            'formality_level': 0.5,
            'response_length': 'medium',
            'conversation_goals': []
        }
        
        # Adapt based on sentiment
        sentiment = basic_analysis.get('sentiment', 'neutral')
        if sentiment == 'negative':
            strategy['response_approach'] = 'supportive'
            strategy['emotional_tone'] = 'empathetic'
        elif sentiment == 'positive':
            strategy['response_approach'] = 'enthusiastic'
            strategy['emotional_tone'] = 'positive'
        
        # Adapt based on conversation type
        conv_type = basic_analysis.get('conversation_type', 'casual_chat')
        if conv_type == 'question':
            strategy['response_approach'] = 'informative'
            strategy['conversation_goals'].append('provide_clear_answer')
        elif conv_type == 'help_request':
            strategy['response_approach'] = 'supportive'
            strategy['conversation_goals'].append('provide_assistance')
        elif conv_type == 'detailed_discussion':
            strategy['response_length'] = 'long'
            strategy['conversation_goals'].append('maintain_depth')
        
        # Adapt based on language
        language = basic_analysis.get('language', 'unknown')
        if language == 'japanese':
            strategy['formality_level'] = 0.7  # Slightly more formal for Japanese
        
        return strategy
    
    def _update_conversation_state(self, conv_id: str, analysis: Dict):
        """Update basic conversation state"""
        if conv_id not in self.conversation_states:
            self.conversation_states[conv_id] = {
                'start_time': datetime.now().isoformat(),
                'turn_count': 0,
                'recent_topics': [],
                'engagement_level': 0.5
            }
        
        state = self.conversation_states[conv_id]
        basic_analysis = analysis.get('basic_analysis', {})
        
        # Update turn count
        state['turn_count'] += 1
        
        # Update recent topics
        topics = basic_analysis.get('topics', [])
        state['recent_topics'].extend(topics)
        if len(state['recent_topics']) > 10:
            state['recent_topics'] = state['recent_topics'][-10:]
        
        # Update engagement based on message characteristics
        message_length = basic_analysis.get('message_length', 0)
        questions = basic_analysis.get('question_count', 0)
        exclamations = basic_analysis.get('exclamation_count', 0)
        
        engagement_score = min(1.0, (message_length / 100.0 + questions * 0.2 + exclamations * 0.1))
        state['engagement_level'] = (state['engagement_level'] * 0.7 + engagement_score * 0.3)