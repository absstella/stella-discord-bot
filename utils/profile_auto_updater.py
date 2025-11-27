"""
Profile Auto-Updater - Automatic profile enhancement from conversations
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
import json
import re
from datetime import datetime
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class ProfileAutoUpdater:
    """Advanced profile auto-updating system that extracts and stores information from conversations"""
    
    def __init__(self):
        # Pattern categories for extraction
        self.extraction_patterns = {
            'personal_info': {
                'age': [r'(\d+)歳', r'(\d+)才', r'age (\d+)', r'im (\d+)', r'(\d+) years old'],
                'location': [r'([都道府県市区町村]+)に住んで', r'([都道府県市区町村]+)在住', r'live in ([A-Za-z\s]+)', r'from ([A-Za-z\s]+)'],
                'occupation': [r'([^\s]+)の仕事', r'([^\s]+)として働', r'work as ([A-Za-z\s]+)', r'job is ([A-Za-z\s]+)'],
                'school': [r'([^\s]+)大学', r'([^\s]+)学校', r'study at ([A-Za-z\s]+)', r'([A-Za-z\s]+) university'],
                'name': [r'私は([^\s]+)です', r'名前は([^\s]+)', r'my name is ([A-Za-z\s]+)', r"i'm ([A-Za-z\s]+)"]
            },
            'preferences': {
                'food': [r'好きな食べ物は([^\s]+)', r'([^\s]+)が好き', r'love ([A-Za-z\s]+)', r'favorite food is ([A-Za-z\s]+)'],
                'music': [r'([^\s]+)を聞く', r'音楽は([^\s]+)', r'listen to ([A-Za-z\s]+)', r'music ([A-Za-z\s]+)'],
                'sports': [r'([^\s]+)をする', r'スポーツは([^\s]+)', r'play ([A-Za-z\s]+)', r'sport is ([A-Za-z\s]+)'],
                'movies': [r'映画は([^\s]+)', r'([^\s]+)という映画', r'movie ([A-Za-z\s]+)', r'film ([A-Za-z\s]+)'],
                'games': [r'ゲームは([^\s]+)', r'([^\s]+)をプレイ', r'play ([A-Za-z\s]+)', r'game ([A-Za-z\s]+)']
            },
            'skills_abilities': {
                'languages': [r'([^\s]+)語ができる', r'([^\s]+)語を話す', r'speak ([A-Za-z]+)', r'language ([A-Za-z]+)'],
                'programming': [r'([^\s]+)を使える', r'プログラミングは([^\s]+)', r'code in ([A-Za-z\s]+)', r'programming ([A-Za-z\s]+)'],
                'instruments': [r'([^\s]+)を弾く', r'楽器は([^\s]+)', r'play ([A-Za-z\s]+) instrument', r'instrument ([A-Za-z\s]+)'],
                'certifications': [r'([^\s]+)の資格', r'([^\s]+)を取得', r'certified in ([A-Za-z\s]+)', r'qualification ([A-Za-z\s]+)']
            },
            'relationships': {
                'family': [r'([^\s]+)がいる', r'家族は([^\s]+)', r'my ([A-Za-z\s]+) is', r'have a ([A-Za-z\s]+)'],
                'friends': [r'友達の([^\s]+)', r'([^\s]+)という友達', r'friend ([A-Za-z\s]+)', r'my friend ([A-Za-z\s]+)'],
                'pets': [r'([^\s]+)を飼って', r'ペットは([^\s]+)', r'pet ([A-Za-z\s]+)', r'have a ([A-Za-z\s]+)']
            },
            'personality': {
                'traits': [r'私は([^\s]+)な人', r'性格は([^\s]+)', r'personality is ([A-Za-z\s]+)', r"i'm ([A-Za-z\s]+) person"],
                'mood': [r'今日は([^\s]+)', r'気分は([^\s]+)', r'feeling ([A-Za-z\s]+)', r'mood is ([A-Za-z\s]+)'],
                'values': [r'大切なのは([^\s]+)', r'価値観は([^\s]+)', r'important is ([A-Za-z\s]+)', r'value ([A-Za-z\s]+)']
            },
            'goals_dreams': {
                'career': [r'将来は([^\s]+)になりたい', r'目標は([^\s]+)', r'want to be ([A-Za-z\s]+)', r'goal is ([A-Za-z\s]+)'],
                'travel': [r'([^\s]+)に行きたい', r'旅行は([^\s]+)', r'want to visit ([A-Za-z\s]+)', r'travel to ([A-Za-z\s]+)'],
                'learning': [r'([^\s]+)を学びたい', r'勉強したいのは([^\s]+)', r'want to learn ([A-Za-z\s]+)', r'study ([A-Za-z\s]+)']
            }
        }
        
        # Context indicators
        self.context_indicators = {
            'past': ['昔', '前に', '以前', 'used to', 'before', 'previously'],
            'present': ['今', '現在', '最近', 'now', 'currently', 'recently'],
            'future': ['将来', '今度', 'これから', 'future', 'plan to', 'will'],
            'uncertain': ['たぶん', 'maybe', 'perhaps', 'might', 'probably'],
            'certain': ['確実に', 'definitely', 'certainly', 'sure']
        }
        
        logger.info("Profile Auto-Updater initialized")
    
    async def analyze_and_update_profile(self, user_profile, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation and automatically update user profile"""
        try:
            update_results = {
                'user_id': conversation_data.get('user_id'),
                'timestamp': datetime.now().isoformat(),
                'new_information': [],
                'updated_fields': [],
                'confidence_scores': {},
                'context_analysis': {}
            }
            
            user_message = conversation_data.get('user_message', '')
            ai_response = conversation_data.get('ai_response', '')
            
            # Extract information from user message
            user_extractions = await self._extract_information(user_message)
            
            # Extract information mentioned about user in AI response
            ai_extractions = await self._extract_user_references(ai_response)
            
            # Combine extractions with confidence weighting
            all_extractions = self._combine_extractions(user_extractions, ai_extractions)
            
            # Update profile with extracted information
            for category, items in all_extractions.items():
                for item_type, values in items.items():
                    for value_data in values:
                        value = value_data['value']
                        confidence = value_data['confidence']
                        context = value_data['context']
                        
                        if confidence > 0.3:  # Minimum confidence threshold
                            updated = await self._update_profile_field(
                                user_profile, category, item_type, value, confidence, context
                            )
                            
                            if updated:
                                update_results['new_information'].append({
                                    'category': category,
                                    'type': item_type,
                                    'value': value,
                                    'confidence': confidence,
                                    'context': context
                                })
                                update_results['updated_fields'].append(f"{category}.{item_type}")
                                update_results['confidence_scores'][f"{category}.{item_type}"] = confidence
            
            # Advanced pattern analysis
            advanced_analysis = await self._advanced_pattern_analysis(user_message, ai_response)
            if advanced_analysis:
                for insight in advanced_analysis:
                    updated = await self._update_profile_insight(user_profile, insight)
                    if updated:
                        update_results['new_information'].append(insight)
            
            # Context and relationship analysis
            context_analysis = await self._analyze_conversation_context(conversation_data)
            update_results['context_analysis'] = context_analysis
            
            # Update communication patterns
            comm_updates = await self._update_communication_patterns(user_profile, user_message)
            update_results['updated_fields'].extend(comm_updates)
            
            return update_results
            
        except Exception as e:
            logger.error(f"Error in profile auto-update: {e}")
            return {
                'user_id': conversation_data.get('user_id'),
                'error': str(e),
                'new_information': []
            }
    
    async def _extract_information(self, text: str) -> Dict[str, Dict[str, List[Dict]]]:
        """Extract structured information from text using patterns"""
        extractions = defaultdict(lambda: defaultdict(list))
        
        text_lower = text.lower()
        
        for category, patterns in self.extraction_patterns.items():
            for item_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, text_lower)
                    for match in matches:
                        value = match.group(1) if match.groups() else match.group(0)
                        confidence = self._calculate_extraction_confidence(value, pattern, text)
                        context = self._determine_context(text, match.start(), match.end())
                        
                        extractions[category][item_type].append({
                            'value': value.strip(),
                            'confidence': confidence,
                            'context': context,
                            'source': 'pattern_match'
                        })
        
        return dict(extractions)
    
    async def _extract_user_references(self, ai_response: str) -> Dict[str, Dict[str, List[Dict]]]:
        """Extract user information mentioned in AI response"""
        extractions = defaultdict(lambda: defaultdict(list))
        
        # Look for information AI mentions about the user
        user_ref_patterns = [
            r'あなたは([^\s]+)',
            r'君は([^\s]+)', 
            r'you are ([A-Za-z\s]+)',
            r'you like ([A-Za-z\s]+)',
            r'you mentioned ([A-Za-z\s]+)'
        ]
        
        for pattern in user_ref_patterns:
            matches = re.finditer(pattern, ai_response.lower())
            for match in matches:
                value = match.group(1).strip()
                confidence = 0.6  # Medium confidence for AI-mentioned info
                
                # Categorize the extracted information
                category = self._categorize_information(value)
                item_type = 'general'
                
                extractions[category][item_type].append({
                    'value': value,
                    'confidence': confidence,
                    'context': 'ai_mentioned',
                    'source': 'ai_response'
                })
        
        return dict(extractions)
    
    def _combine_extractions(self, user_extractions: Dict, ai_extractions: Dict) -> Dict:
        """Combine extractions from user and AI with appropriate weighting"""
        combined = defaultdict(lambda: defaultdict(list))
        
        # Add user extractions with full weight
        for category, items in user_extractions.items():
            for item_type, values in items.items():
                combined[category][item_type].extend(values)
        
        # Add AI extractions with reduced weight
        for category, items in ai_extractions.items():
            for item_type, values in items.items():
                for value_data in values:
                    value_data['confidence'] *= 0.7  # Reduce confidence for AI-mentioned info
                    combined[category][item_type].append(value_data)
        
        return dict(combined)
    
    def _calculate_extraction_confidence(self, value: str, pattern: str, full_text: str) -> float:
        """Calculate confidence score for extracted information"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for longer, more specific values
        if len(value) > 5:
            confidence += 0.2
        
        # Increase confidence for first-person statements
        if any(indicator in full_text.lower() for indicator in ['私は', 'i am', 'my', '僕は']):
            confidence += 0.3
        
        # Decrease confidence for uncertain language
        if any(indicator in full_text.lower() for indicator in self.context_indicators['uncertain']):
            confidence -= 0.2
        
        # Increase confidence for definitive language
        if any(indicator in full_text.lower() for indicator in self.context_indicators['certain']):
            confidence += 0.2
        
        return min(max(confidence, 0.0), 1.0)
    
    def _determine_context(self, text: str, start_pos: int, end_pos: int) -> str:
        """Determine temporal context of extracted information"""
        context_window = text[max(0, start_pos-50):min(len(text), end_pos+50)].lower()
        
        for context_type, indicators in self.context_indicators.items():
            if any(indicator in context_window for indicator in indicators):
                return context_type
        
        return 'present'  # Default to present context
    
    def _categorize_information(self, value: str) -> str:
        """Categorize extracted information into appropriate category"""
        value_lower = value.lower()
        
        # Simple categorization rules
        if any(word in value_lower for word in ['happy', 'sad', 'angry', '楽しい', '悲しい']):
            return 'personality'
        elif any(word in value_lower for word in ['work', 'job', '仕事', '会社']):
            return 'personal_info'
        elif any(word in value_lower for word in ['like', 'love', 'hate', '好き', '嫌い']):
            return 'preferences'
        elif any(word in value_lower for word in ['friend', 'family', '友達', '家族']):
            return 'relationships'
        else:
            return 'personal_info'  # Default category
    
    async def _update_profile_field(self, profile, category: str, item_type: str, value: str, confidence: float, context: str) -> bool:
        """Update specific profile field with new information"""
        try:
            # Get or create category in profile
            if not hasattr(profile, 'auto_extracted_info'):
                profile.auto_extracted_info = {}
            
            if category not in profile.auto_extracted_info:
                profile.auto_extracted_info[category] = {}
            
            if item_type not in profile.auto_extracted_info[category]:
                profile.auto_extracted_info[category][item_type] = []
            
            # Check if this information already exists
            existing_values = [item['value'] for item in profile.auto_extracted_info[category][item_type]]
            
            if value not in existing_values:
                # Add new information
                profile.auto_extracted_info[category][item_type].append({
                    'value': value,
                    'confidence': confidence,
                    'context': context,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'auto_extraction'
                })
                
                # Also add to traditional profile fields for compatibility
                await self._update_traditional_fields(profile, category, item_type, value)
                
                return True
            else:
                # Update confidence if higher
                for item in profile.auto_extracted_info[category][item_type]:
                    if item['value'] == value and item['confidence'] < confidence:
                        item['confidence'] = confidence
                        item['timestamp'] = datetime.now().isoformat()
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating profile field: {e}")
            return False
    
    async def _update_traditional_fields(self, profile, category: str, item_type: str, value: str):
        """Update traditional profile fields for backward compatibility"""
        try:
            # Map new categories to existing profile fields
            if category == 'personal_info':
                if item_type == 'age':
                    profile.add_personal_trait(f"年齢: {value}")
                elif item_type == 'location':
                    profile.add_personal_trait(f"居住地: {value}")
                elif item_type == 'occupation':
                    profile.add_personal_trait(f"職業: {value}")
                elif item_type == 'name':
                    profile.add_personal_trait(f"名前: {value}")
            
            elif category == 'preferences':
                profile.add_interest(f"{item_type}: {value}")
            
            elif category == 'skills_abilities':
                profile.add_behavioral_trait(f"{item_type}: {value}")
            
            elif category == 'personality':
                profile.add_behavioral_trait(f"性格: {value}")
            
            elif category == 'relationships':
                profile.add_personal_trait(f"{item_type}: {value}")
            
        except Exception as e:
            logger.debug(f"Error updating traditional fields: {e}")
    
    async def _advanced_pattern_analysis(self, user_message: str, ai_response: str) -> List[Dict]:
        """Perform advanced pattern analysis for complex information extraction"""
        insights = []
        
        try:
            # Analyze sentiment and emotional patterns
            emotion_analysis = await self._analyze_emotional_patterns(user_message)
            if emotion_analysis:
                insights.append({
                    'category': 'emotional_state',
                    'type': 'current_emotion',
                    'value': emotion_analysis,
                    'confidence': 0.7,
                    'context': 'present'
                })
            
            # Analyze communication style
            style_analysis = await self._analyze_communication_style(user_message)
            if style_analysis:
                insights.append({
                    'category': 'communication',
                    'type': 'style',
                    'value': style_analysis,
                    'confidence': 0.8,
                    'context': 'general'
                })
            
            # Analyze interests from context
            interest_analysis = await self._extract_contextual_interests(user_message, ai_response)
            for interest in interest_analysis:
                insights.append({
                    'category': 'preferences',
                    'type': 'contextual_interest',
                    'value': interest,
                    'confidence': 0.6,
                    'context': 'inferred'
                })
            
        except Exception as e:
            logger.error(f"Error in advanced pattern analysis: {e}")
        
        return insights
    
    async def _analyze_emotional_patterns(self, text: str) -> str:
        """Analyze emotional patterns in text"""
        emotions = {
            'happy': ['嬉しい', '楽しい', 'happy', 'excited', 'glad', 'joy'],
            'sad': ['悲しい', 'つらい', 'sad', 'depressed', 'upset'],
            'angry': ['怒り', '腹立つ', 'angry', 'mad', 'frustrated'],
            'anxious': ['不安', '心配', 'anxious', 'worried', 'nervous'],
            'calm': ['落ち着い', '穏やか', 'calm', 'peaceful', 'relaxed']
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in emotions.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        return None
    
    async def _analyze_communication_style(self, text: str) -> str:
        """Analyze communication style from text"""
        style_indicators = {
            'formal': ['です', 'ます', 'ございます', 'いたします'],
            'casual': ['だよ', 'だね', 'じゃん', 'ってか'],
            'enthusiastic': ['！', '!', 'すごい', 'amazing', 'awesome'],
            'detailed': ['詳しく', 'specifically', 'exactly', '具体的に'],
            'concise': ['簡単に', 'briefly', 'short']
        }
        
        text_lower = text.lower()
        style_scores = {}
        
        for style, indicators in style_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                style_scores[style] = score
        
        if style_scores:
            return max(style_scores, key=style_scores.get)
        
        return None
    
    async def _extract_contextual_interests(self, user_message: str, ai_response: str) -> List[str]:
        """Extract interests from conversation context"""
        interests = []
        
        # Look for topics discussed extensively
        combined_text = f"{user_message} {ai_response}".lower()
        
        topic_keywords = {
            'technology': ['ai', 'computer', 'programming', 'tech', 'コンピュータ', 'プログラミング'],
            'music': ['music', 'song', 'band', 'album', '音楽', '歌'],
            'sports': ['sport', 'game', 'team', 'play', 'スポーツ', 'ゲーム'],
            'travel': ['travel', 'country', 'city', 'trip', '旅行', '国'],
            'food': ['food', 'restaurant', 'cook', 'eat', '食べ物', '料理'],
            'movies': ['movie', 'film', 'cinema', 'watch', '映画']
        }
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score >= 2:  # Multiple mentions indicate interest
                interests.append(topic)
        
        return interests
    
    async def _analyze_conversation_context(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall conversation context"""
        context = {
            'conversation_length': len(conversation_data.get('user_message', '')),
            'question_type': self._classify_question_type(conversation_data.get('user_message', '')),
            'engagement_level': self._assess_engagement_level(conversation_data),
            'topic_complexity': self._assess_topic_complexity(conversation_data.get('user_message', ''))
        }
        
        return context
    
    def _classify_question_type(self, message: str) -> str:
        """Classify the type of question/message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['what', 'なに', '何']):
            return 'what_question'
        elif any(word in message_lower for word in ['how', 'どう', 'どのよう']):
            return 'how_question'
        elif any(word in message_lower for word in ['why', 'なぜ', 'どうして']):
            return 'why_question'
        elif any(word in message_lower for word in ['when', 'いつ']):
            return 'when_question'
        elif any(word in message_lower for word in ['where', 'どこ']):
            return 'where_question'
        elif '?' in message or '？' in message:
            return 'general_question'
        else:
            return 'statement'
    
    def _assess_engagement_level(self, conversation_data: Dict[str, Any]) -> str:
        """Assess user engagement level"""
        user_message = conversation_data.get('user_message', '')
        message_length = len(user_message)
        
        if message_length > 100:
            return 'high'
        elif message_length > 30:
            return 'medium'
        else:
            return 'low'
    
    def _assess_topic_complexity(self, message: str) -> str:
        """Assess complexity of topics discussed"""
        complex_indicators = ['技術', 'アルゴリズム', 'システム', 'technical', 'algorithm', 'complex', 'advanced']
        simple_indicators = ['簡単', 'easy', 'simple', 'basic']
        
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in complex_indicators):
            return 'high'
        elif any(indicator in message_lower for indicator in simple_indicators):
            return 'low'
        else:
            return 'medium'
    
    async def _update_communication_patterns(self, profile, message: str) -> List[str]:
        """Update communication patterns in profile"""
        updates = []
        
        try:
            # Analyze message patterns
            patterns = {
                'message_length': 'long' if len(message) > 50 else 'short',
                'emoji_usage': 'high' if message.count('😊') + message.count('🎉') > 0 else 'low',
                'punctuation': 'enthusiastic' if '!' in message or '！' in message else 'calm'
            }
            
            # Update profile with communication patterns
            if not hasattr(profile, 'communication_patterns'):
                profile.communication_patterns = {}
            
            for pattern_type, pattern_value in patterns.items():
                profile.communication_patterns[pattern_type] = pattern_value
                updates.append(f"communication.{pattern_type}")
        
        except Exception as e:
            logger.error(f"Error updating communication patterns: {e}")
        
        return updates
    
    async def _update_profile_insight(self, profile, insight: Dict[str, Any]) -> bool:
        """Update profile with advanced insights"""
        try:
            category = insight['category']
            item_type = insight['type']
            value = insight['value']
            confidence = insight['confidence']
            
            return await self._update_profile_field(profile, category, item_type, value, confidence, insight.get('context', 'general'))
        
        except Exception as e:
            logger.error(f"Error updating profile insight: {e}")
            return False
    
    def get_profile_update_summary(self, update_results: Dict[str, Any]) -> str:
        """Generate human-readable summary of profile updates"""
        if not update_results.get('new_information'):
            return "新しい情報は見つかりませんでした。"
        
        summary_parts = []
        new_info = update_results['new_information']
        
        # Group by category
        categories = {}
        for info in new_info:
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(info)
        
        for category, items in categories.items():
            category_name = {
                'personal_info': '個人情報',
                'preferences': '好み',
                'skills_abilities': 'スキル・能力',
                'personality': '性格',
                'relationships': '人間関係',
                'goals_dreams': '目標・夢',
                'emotional_state': '感情状態',
                'communication': 'コミュニケーション'
            }.get(category, category)
            
            item_list = [f"・{item['value']}" for item in items]
            summary_parts.append(f"{category_name}: {', '.join([item['value'] for item in items])}")
        
        return f"プロフィールに追加された情報: {'; '.join(summary_parts)}"

# Global instance
profile_auto_updater = ProfileAutoUpdater()