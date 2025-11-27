"""
Aggressive Profile Expander - Enhanced automatic profile expansion with proactive information addition
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

class AggressiveProfileExpander:
    """Proactively expands user profiles with any detectable information"""
    
    def __init__(self):
        # Enhanced extraction patterns with lower thresholds
        self.behavior_indicators = {
            'time_patterns': {
                'night_owl': ['夜', '深夜', 'late night', 'midnight', '12時', '1時', '2時'],
                'early_bird': ['朝', '早起き', 'morning', 'early', '6時', '7時', '8時'],
                'weekend_active': ['土曜', '日曜', 'weekend', 'saturday', 'sunday'],
                'workday_focus': ['平日', 'weekday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            },
            'communication_style': {
                'direct': ['直接', 'straightforward', 'direct', 'はっきり'],
                'polite': ['丁寧', 'polite', 'respectful', 'すみません', 'ありがとう'],
                'casual': ['カジュアル', 'casual', 'relaxed', 'だよ', 'じゃん'],
                'analytical': ['分析', 'analysis', 'データ', 'data', '統計'],
                'creative': ['創造', 'creative', 'アート', 'art', 'デザイン']
            },
            'learning_style': {
                'visual': ['図', 'グラフ', 'visual', 'chart', 'diagram', '見る'],
                'hands_on': ['実践', 'hands-on', 'practice', '試す', 'やってみる'],
                'theoretical': ['理論', 'theory', 'concept', '概念', '原理'],
                'step_by_step': ['段階', 'step', 'ステップ', '順番', '手順']
            },
            'work_style': {
                'multitasker': ['マルチタスク', 'multitask', '同時', '並行'],
                'focused': ['集中', 'focus', '一つずつ', 'one thing'],
                'collaborative': ['協力', 'collaborate', 'チーム', 'team'],
                'independent': ['独立', 'independent', '一人で', 'solo']
            }
        }
        
        # Comprehensive interest detection
        self.interest_domains = {
            'technology': {
                'programming': ['プログラミング', 'programming', 'code', 'コード', 'python', 'javascript', 'java'],
                'ai_ml': ['AI', 'ML', '機械学習', 'machine learning', 'neural', 'ニューラル'],
                'gaming': ['ゲーム', 'game', 'gaming', 'プレイ', 'play'],
                'hardware': ['ハードウェア', 'hardware', 'pc', 'cpu', 'gpu'],
                'software': ['ソフトウェア', 'software', 'app', 'アプリ', 'tool']
            },
            'creative': {
                'art': ['アート', 'art', '絵', 'drawing', 'イラスト'],
                'music': ['音楽', 'music', '歌', 'song', '楽器'],
                'writing': ['執筆', 'writing', '小説', 'novel', 'ブログ'],
                'design': ['デザイン', 'design', 'UI', 'UX', 'グラフィック'],
                'photography': ['写真', 'photography', 'カメラ', 'camera']
            },
            'lifestyle': {
                'fitness': ['運動', 'fitness', 'ジム', 'gym', 'トレーニング'],
                'cooking': ['料理', 'cooking', '作る', 'レシピ', 'recipe'],
                'travel': ['旅行', 'travel', '観光', 'tourism', '国'],
                'reading': ['読書', 'reading', '本', 'book', '小説'],
                'movies': ['映画', 'movie', 'film', '観る', 'watch']
            },
            'social': {
                'community': ['コミュニティ', 'community', '仲間', 'group'],
                'teaching': ['教える', 'teaching', '指導', 'mentor'],
                'helping': ['手伝い', 'help', 'サポート', 'support'],
                'organizing': ['企画', 'organize', '準備', 'plan']
            }
        }
        
        # Personality trait inference patterns
        self.personality_patterns = {
            'analytical': ['分析', '考える', 'think', 'analyze', 'データ', '論理'],
            'creative': ['創造', 'creative', 'アイデア', 'idea', '新しい'],
            'organized': ['整理', 'organize', '計画', 'plan', 'スケジュール'],
            'spontaneous': ['突然', 'spontaneous', '思いつき', 'impulsive'],
            'social': ['人と', 'social', '友達', 'friend', 'みんな'],
            'introverted': ['一人', 'alone', '静か', 'quiet', '内向'],
            'optimistic': ['前向き', 'positive', '楽観', 'optimistic'],
            'detail_oriented': ['詳細', 'detail', '細かい', 'precise'],
            'big_picture': ['全体', 'big picture', '概要', 'overall'],
            'practical': ['実用', 'practical', '現実', 'realistic'],
            'curious': ['好奇心', 'curious', '興味', 'interested', '知りたい'],
            'patient': ['忍耐', 'patient', '待つ', 'wait', 'ゆっくり'],
            'energetic': ['エネルギー', 'energetic', '活発', 'active']
        }

    async def expand_profile_aggressively(self, user_profile, user_message: str, ai_response: str, conversation_context: Dict = None) -> Dict[str, Any]:
        """Aggressively expand profile with any detectable information"""
        expansion_results = {
            'new_traits': [],
            'new_interests': [],
            'new_behaviors': [],
            'new_preferences': [],
            'updated_attributes': [],
            'confidence_scores': {}
        }
        
        try:
            combined_text = f"{user_message} {ai_response}"
            
            # 1. Aggressive personality trait detection
            new_traits = await self._detect_personality_traits(user_message, ai_response)
            for trait in new_traits:
                if trait not in user_profile.personality_traits:
                    user_profile.personality_traits.append(trait)
                    expansion_results['new_traits'].append(trait)
                    logger.info(f"Added personality trait: {trait}")
            
            # 2. Enhanced interest detection
            new_interests = await self._detect_comprehensive_interests(combined_text)
            for interest in new_interests:
                if interest not in user_profile.interests:
                    user_profile.interests.append(interest)
                    expansion_results['new_interests'].append(interest)
                    logger.info(f"Added interest: {interest}")
            
            # 3. Behavioral pattern detection
            behaviors = await self._detect_behavioral_patterns(user_message, ai_response, conversation_context)
            for behavior_type, behavior_value in behaviors.items():
                attr_key = f"behavior_{behavior_type}"
                user_profile.add_custom_attribute(attr_key, behavior_value)
                expansion_results['new_behaviors'].append({behavior_type: behavior_value})
                expansion_results['updated_attributes'].append(attr_key)
            
            # 4. Time and activity pattern detection
            time_patterns = await self._detect_time_activity_patterns(user_message, conversation_context)
            for pattern_type, pattern_data in time_patterns.items():
                attr_key = f"time_pattern_{pattern_type}"
                user_profile.add_custom_attribute(attr_key, pattern_data)
                expansion_results['updated_attributes'].append(attr_key)
            
            # 5. Communication preference detection
            comm_prefs = await self._detect_communication_preferences(user_message, ai_response)
            for pref_type, pref_value in comm_prefs.items():
                attr_key = f"comm_pref_{pref_type}"
                user_profile.add_custom_attribute(attr_key, pref_value)
                expansion_results['updated_attributes'].append(attr_key)
            
            # 6. Learning style detection
            learning_styles = await self._detect_learning_styles(user_message, ai_response)
            for style_type, style_data in learning_styles.items():
                attr_key = f"learning_style_{style_type}"
                user_profile.add_custom_attribute(attr_key, style_data)
                expansion_results['updated_attributes'].append(attr_key)
            
            # 7. Mood and emotional state tracking
            emotional_data = await self._track_emotional_states(user_message, ai_response)
            for emotion_type, emotion_data in emotional_data.items():
                attr_key = f"emotion_{emotion_type}"
                user_profile.add_custom_attribute(attr_key, emotion_data)
                expansion_results['updated_attributes'].append(attr_key)
            
            # 8. Preference inference from context
            preferences = await self._infer_preferences(combined_text)
            for pref_category, pref_items in preferences.items():
                attr_key = f"preference_{pref_category}"
                existing = user_profile.get_custom_attribute(attr_key, [])
                if isinstance(existing, list):
                    for item in pref_items:
                        if item not in existing:
                            existing.append(item)
                else:
                    existing = pref_items
                user_profile.add_custom_attribute(attr_key, existing)
                expansion_results['new_preferences'].append({pref_category: pref_items})
                expansion_results['updated_attributes'].append(attr_key)
            
            # 9. Skill and knowledge area detection
            skills = await self._detect_skills_knowledge(user_message, ai_response)
            for skill_area, skill_level in skills.items():
                attr_key = f"skill_{skill_area}"
                user_profile.add_custom_attribute(attr_key, skill_level)
                expansion_results['updated_attributes'].append(attr_key)
            
            # 10. Social interaction pattern analysis
            social_patterns = await self._analyze_social_patterns(user_message, conversation_context)
            for pattern_type, pattern_value in social_patterns.items():
                attr_key = f"social_{pattern_type}"
                user_profile.add_custom_attribute(attr_key, pattern_value)
                expansion_results['updated_attributes'].append(attr_key)
            
            logger.info(f"Aggressive profile expansion completed: {len(expansion_results['new_traits'])} traits, "
                       f"{len(expansion_results['new_interests'])} interests, "
                       f"{len(expansion_results['updated_attributes'])} attributes updated")
            
            return expansion_results
            
        except Exception as e:
            logger.error(f"Error in aggressive profile expansion: {e}")
            return expansion_results

    async def _detect_personality_traits(self, user_message: str, ai_response: str) -> List[str]:
        """Detect personality traits from conversation patterns"""
        traits = []
        text = f"{user_message} {ai_response}".lower()
        
        for trait, indicators in self.personality_patterns.items():
            score = sum(1 for indicator in indicators if indicator in text)
            if score >= 1:  # Very low threshold for inclusion
                traits.append(trait)
        
        # Additional context-based trait detection
        if len(user_message) > 100:
            traits.append("詳細志向")
        if '?' in user_message or '？' in user_message:
            traits.append("探究心旺盛")
        if any(word in user_message.lower() for word in ['thanks', 'ありがとう', 'thank you']):
            traits.append("礼儀正しい")
        
        return traits

    async def _detect_comprehensive_interests(self, text: str) -> List[str]:
        """Comprehensive interest detection from any mention"""
        interests = []
        text_lower = text.lower()
        
        for domain, categories in self.interest_domains.items():
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score >= 1:  # Single mention is enough
                    interests.append(category)
                    if score >= 2:  # Multiple mentions suggest strong interest
                        interests.append(f"{category}_enthusiast")
        
        return interests

    async def _detect_behavioral_patterns(self, user_message: str, ai_response: str, context: Dict = None) -> Dict[str, Any]:
        """Detect behavioral patterns from conversation"""
        behaviors = {}
        text = f"{user_message} {ai_response}".lower()
        
        for behavior_category, patterns in self.behavior_indicators.items():
            for pattern_name, indicators in patterns.items():
                score = sum(1 for indicator in indicators if indicator in text)
                if score >= 1:
                    behaviors[f"{behavior_category}_{pattern_name}"] = {
                        'detected': True,
                        'confidence': min(score * 0.3, 1.0),
                        'timestamp': datetime.now().isoformat()
                    }
        
        return behaviors

    async def _detect_time_activity_patterns(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Detect time-based activity patterns"""
        patterns = {}
        
        if context and 'timestamp' in context:
            hour = datetime.fromisoformat(context['timestamp']).hour
            
            if 22 <= hour or hour <= 5:
                patterns['night_activity'] = {
                    'active_hours': [hour],
                    'pattern': 'night_owl',
                    'confidence': 0.7
                }
            elif 6 <= hour <= 9:
                patterns['morning_activity'] = {
                    'active_hours': [hour],
                    'pattern': 'early_bird',
                    'confidence': 0.7
                }
        
        # Message length analysis
        if len(user_message) > 200:
            patterns['detailed_communication'] = {
                'tendency': 'verbose',
                'confidence': 0.6
            }
        elif len(user_message) < 50:
            patterns['concise_communication'] = {
                'tendency': 'brief',
                'confidence': 0.6
            }
        
        return patterns

    async def _detect_communication_preferences(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Detect communication style preferences"""
        preferences = {}
        
        # Formality detection
        formal_indicators = ['です', 'ます', 'ございます']
        casual_indicators = ['だよ', 'だね', 'じゃん']
        
        formal_score = sum(1 for indicator in formal_indicators if indicator in user_message)
        casual_score = sum(1 for indicator in casual_indicators if indicator in user_message)
        
        if formal_score > casual_score:
            preferences['formality'] = 'formal'
        elif casual_score > formal_score:
            preferences['formality'] = 'casual'
        else:
            preferences['formality'] = 'mixed'
        
        # Directness detection
        if any(word in user_message.lower() for word in ['please', 'お願い', 'could you']):
            preferences['directness'] = 'polite'
        elif user_message.startswith(('!', '/', 'show', '表示')):
            preferences['directness'] = 'direct'
        
        return preferences

    async def _detect_learning_styles(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Detect preferred learning styles"""
        styles = {}
        text = f"{user_message} {ai_response}".lower()
        
        for style_category, patterns in self.behavior_indicators['learning_style'].items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score >= 1:
                styles[style_category] = {
                    'preference': True,
                    'confidence': min(score * 0.4, 1.0),
                    'detected_from': 'conversation'
                }
        
        return styles

    async def _track_emotional_states(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Track emotional states and patterns"""
        emotions = {}
        
        # Emotion detection patterns
        emotion_indicators = {
            'excitement': ['!', '！', 'すごい', 'amazing', 'awesome', '嬉しい'],
            'confusion': ['?', '？', 'わからない', "don't understand", 'confused'],
            'satisfaction': ['良い', 'good', 'thanks', 'ありがとう', '助かる'],
            'frustration': ['難しい', 'difficult', 'hard', '困る', 'stuck'],
            'curiosity': ['興味', 'interesting', '面白い', 'curious', 'もっと']
        }
        
        for emotion, indicators in emotion_indicators.items():
            score = sum(1 for indicator in indicators if indicator in user_message.lower())
            if score >= 1:
                emotions[emotion] = {
                    'detected': True,
                    'intensity': min(score * 0.3, 1.0),
                    'timestamp': datetime.now().isoformat(),
                    'context': user_message[:50] + '...' if len(user_message) > 50 else user_message
                }
        
        return emotions

    async def _infer_preferences(self, text: str) -> Dict[str, List[str]]:
        """Infer preferences from any mention or context"""
        preferences = defaultdict(list)
        text_lower = text.lower()
        
        # Technology preferences
        tech_terms = ['python', 'javascript', 'ai', 'ml', 'discord', 'github', 'vscode']
        for term in tech_terms:
            if term in text_lower:
                preferences['technology'].append(term)
        
        # Platform preferences
        platforms = ['discord', 'twitter', 'github', 'youtube', 'twitch']
        for platform in platforms:
            if platform in text_lower:
                preferences['platforms'].append(platform)
        
        # Time preferences
        time_terms = ['morning', '朝', 'night', '夜', 'weekend', '週末']
        for term in time_terms:
            if term in text_lower:
                preferences['time'].append(term)
        
        return dict(preferences)

    async def _detect_skills_knowledge(self, user_message: str, ai_response: str) -> Dict[str, str]:
        """Detect skills and knowledge areas"""
        skills = {}
        text = f"{user_message} {ai_response}".lower()
        
        skill_indicators = {
            'programming': ['code', 'プログラム', 'develop', '開発'],
            'design': ['design', 'デザイン', 'ui', 'ux'],
            'music': ['music', '音楽', 'song', '歌'],
            'language': ['english', '英語', 'japanese', '日本語'],
            'gaming': ['game', 'ゲーム', 'play', 'プレイ']
        }
        
        for skill, indicators in skill_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            if score >= 1:
                if score >= 3:
                    skills[skill] = 'advanced'
                elif score >= 2:
                    skills[skill] = 'intermediate'
                else:
                    skills[skill] = 'beginner'
        
        return skills

    async def _analyze_social_patterns(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Analyze social interaction patterns"""
        patterns = {}
        
        # Question asking behavior
        if '?' in user_message or '？' in user_message:
            patterns['question_frequency'] = {
                'asks_questions': True,
                'pattern': 'inquisitive'
            }
        
        # Collaboration indicators
        if any(word in user_message.lower() for word in ['help', 'together', '一緒', '手伝い']):
            patterns['collaboration'] = {
                'collaborative': True,
                'pattern': 'team_oriented'
            }
        
        # Leadership indicators
        if any(word in user_message.lower() for word in ['manage', 'lead', '管理', 'organize']):
            patterns['leadership'] = {
                'shows_leadership': True,
                'pattern': 'organizer'
            }
        
        return patterns