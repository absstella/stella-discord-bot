"""
Emotion Analysis and Psychological State Tracking System
Advanced emotion recognition and mood tracking for user conversations
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import google.generativeai as genai

logger = logging.getLogger(__name__)

@dataclass
class EmotionState:
    """Represents a user's emotional state at a specific time"""
    timestamp: datetime
    primary_emotion: str
    emotion_intensity: float  # 0.0 - 1.0
    secondary_emotions: List[str] = field(default_factory=list)
    mood_score: float = 0.0  # -1.0 (very negative) to 1.0 (very positive)
    stress_level: float = 0.0  # 0.0 - 1.0
    energy_level: float = 0.5  # 0.0 - 1.0
    context: str = ""
    triggers: List[str] = field(default_factory=list)

@dataclass
class EmotionTrend:
    """Represents emotion trends over time"""
    timeframe: str  # "daily", "weekly", "monthly"
    dominant_emotions: List[str]
    average_mood: float
    mood_stability: float
    stress_patterns: List[str]
    improvement_areas: List[str]

class EmotionAnalyzer:
    """Advanced emotion analysis and psychological state tracking"""
    
    def __init__(self):
        self.gemini_model = None
        self.emotion_data_dir = "data/emotions"
        
        # Initialize Gemini for emotion analysis
        try:
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("Emotion Analyzer with Gemini initialized")
            else:
                logger.warning("GEMINI_API_KEY not found for emotion analysis")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for emotion analysis: {e}")
        
        # Create emotion data directory
        os.makedirs(self.emotion_data_dir, exist_ok=True)
        
        # Emotion categories and patterns
        self.emotion_categories = {
            "positive": [
                "喜び", "幸せ", "満足", "感謝", "興奮", "希望", "愛情", "平和",
                "自信", "安心", "楽しい", "嬉しい", "ワクワク", "リラックス"
            ],
            "negative": [
                "悲しい", "怒り", "不安", "恐怖", "失望", "孤独", "疲労", "ストレス",
                "イライラ", "心配", "落ち込み", "絶望", "混乱", "嫉妬"
            ],
            "neutral": [
                "普通", "平静", "冷静", "集中", "思考", "考察", "分析", "観察"
            ]
        }
        
        # Stress indicators
        self.stress_indicators = [
            "疲れた", "しんどい", "大変", "忙しい", "キツい", "辛い", "難しい",
            "プレッシャー", "締切", "仕事", "勉強", "試験", "心配", "不安"
        ]
        
        # Energy indicators
        self.high_energy_indicators = [
            "やる気", "元気", "活発", "テンション", "ハイ", "頑張る", "挑戦",
            "！", "!!", "やったー", "最高", "すごい", "わーい"
        ]
        
        self.low_energy_indicators = [
            "疲れ", "だるい", "眠い", "やる気がない", "無気力", "ぼーっと",
            "めんどくさい", "しんどい", "重い", "動きたくない"
        ]

    async def analyze_emotion(self, message: str, user_id: int, context: Dict = None) -> EmotionState:
        """Analyze emotion from a message"""
        try:
            # Use AI-powered emotion analysis if available
            if self.gemini_model:
                emotion_state = await self._ai_emotion_analysis(message, context)
            else:
                emotion_state = await self._rule_based_emotion_analysis(message)
            
            # Save emotion state
            await self._save_emotion_state(user_id, emotion_state)
            
            return emotion_state
            
        except Exception as e:
            logger.error(f"Error analyzing emotion: {e}")
            return EmotionState(
                timestamp=datetime.now(),
                primary_emotion="neutral",
                emotion_intensity=0.5,
                mood_score=0.0
            )

    async def _ai_emotion_analysis(self, message: str, context: Dict = None) -> EmotionState:
        """AI-powered emotion analysis using Gemini"""
        try:
            analysis_prompt = f"""
以下のメッセージから感情状態を詳細に分析してください。

メッセージ: {message}

以下の形式でJSON出力してください：
{{
  "primary_emotion": "主要感情（日本語）",
  "emotion_intensity": 0.8,
  "secondary_emotions": ["副次的感情1", "副次的感情2"],
  "mood_score": 0.5,
  "stress_level": 0.3,
  "energy_level": 0.7,
  "context_analysis": "文脈の説明",
  "triggers": ["感情の要因1", "要因2"]
}}

感情分析の基準：
- primary_emotion: 最も強い感情（喜び、悲しい、怒り、不安、興奮、疲労など）
- emotion_intensity: 感情の強さ（0.0-1.0）
- mood_score: 全体的な気分（-1.0 = とても否定的、0.0 = 中性、1.0 = とても肯定的）
- stress_level: ストレスレベル（0.0-1.0）
- energy_level: エネルギーレベル（0.0-1.0）
"""
            
            response = self.gemini_model.generate_content(analysis_prompt)
            
            if response and response.text:
                try:
                    # Parse JSON response
                    emotion_data = json.loads(response.text)
                    
                    return EmotionState(
                        timestamp=datetime.now(),
                        primary_emotion=emotion_data.get("primary_emotion", "neutral"),
                        emotion_intensity=float(emotion_data.get("emotion_intensity", 0.5)),
                        secondary_emotions=emotion_data.get("secondary_emotions", []),
                        mood_score=float(emotion_data.get("mood_score", 0.0)),
                        stress_level=float(emotion_data.get("stress_level", 0.0)),
                        energy_level=float(emotion_data.get("energy_level", 0.5)),
                        context=emotion_data.get("context_analysis", ""),
                        triggers=emotion_data.get("triggers", [])
                    )
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI emotion analysis JSON")
                    return await self._rule_based_emotion_analysis(message)
            
        except Exception as e:
            logger.error(f"Error in AI emotion analysis: {e}")
            
        return await self._rule_based_emotion_analysis(message)

    async def _rule_based_emotion_analysis(self, message: str) -> EmotionState:
        """Fallback rule-based emotion analysis"""
        message_lower = message.lower()
        
        # Detect primary emotion
        primary_emotion = "neutral"
        emotion_intensity = 0.5
        secondary_emotions = []
        
        # Check for positive emotions
        positive_count = sum(1 for emotion in self.emotion_categories["positive"] 
                           if emotion in message_lower)
        
        # Check for negative emotions
        negative_count = sum(1 for emotion in self.emotion_categories["negative"] 
                           if emotion in message_lower)
        
        if positive_count > negative_count:
            primary_emotion = "喜び"
            emotion_intensity = min(0.3 + (positive_count * 0.2), 1.0)
        elif negative_count > positive_count:
            primary_emotion = "悲しい"
            emotion_intensity = min(0.3 + (negative_count * 0.2), 1.0)
        
        # Calculate mood score
        mood_score = (positive_count - negative_count) * 0.2
        mood_score = max(-1.0, min(1.0, mood_score))
        
        # Calculate stress level
        stress_count = sum(1 for indicator in self.stress_indicators 
                         if indicator in message_lower)
        stress_level = min(stress_count * 0.3, 1.0)
        
        # Calculate energy level
        high_energy_count = sum(1 for indicator in self.high_energy_indicators 
                              if indicator in message_lower)
        low_energy_count = sum(1 for indicator in self.low_energy_indicators 
                             if indicator in message_lower)
        
        energy_level = 0.5 + (high_energy_count * 0.2) - (low_energy_count * 0.2)
        energy_level = max(0.0, min(1.0, energy_level))
        
        return EmotionState(
            timestamp=datetime.now(),
            primary_emotion=primary_emotion,
            emotion_intensity=emotion_intensity,
            mood_score=mood_score,
            stress_level=stress_level,
            energy_level=energy_level,
            context=f"Message analysis: {message[:50]}..."
        )

    async def get_emotion_history(self, user_id: int, days: int = 7) -> List[EmotionState]:
        """Get emotion history for a user"""
        try:
            emotion_file = os.path.join(self.emotion_data_dir, f"user_{user_id}.json")
            
            if not os.path.exists(emotion_file):
                return []
            
            with open(emotion_file, 'r', encoding='utf-8') as f:
                emotion_data = json.load(f)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_emotions = []
            
            for emotion_dict in emotion_data.get('emotions', []):
                emotion_timestamp = datetime.fromisoformat(emotion_dict['timestamp'])
                if emotion_timestamp >= cutoff_date:
                    emotion_state = EmotionState(
                        timestamp=emotion_timestamp,
                        primary_emotion=emotion_dict.get('primary_emotion', 'neutral'),
                        emotion_intensity=emotion_dict.get('emotion_intensity', 0.5),
                        secondary_emotions=emotion_dict.get('secondary_emotions', []),
                        mood_score=emotion_dict.get('mood_score', 0.0),
                        stress_level=emotion_dict.get('stress_level', 0.0),
                        energy_level=emotion_dict.get('energy_level', 0.5),
                        context=emotion_dict.get('context', ''),
                        triggers=emotion_dict.get('triggers', [])
                    )
                    recent_emotions.append(emotion_state)
            
            return sorted(recent_emotions, key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting emotion history: {e}")
            return []

    async def analyze_emotion_trends(self, user_id: int, timeframe: str = "weekly") -> EmotionTrend:
        """Analyze emotion trends over time"""
        try:
            if timeframe == "daily":
                days = 1
            elif timeframe == "weekly":
                days = 7
            elif timeframe == "monthly":
                days = 30
            else:
                days = 7
            
            emotions = await self.get_emotion_history(user_id, days)
            
            if not emotions:
                return EmotionTrend(
                    timeframe=timeframe,
                    dominant_emotions=["データなし"],
                    average_mood=0.0,
                    mood_stability=0.0,
                    stress_patterns=[],
                    improvement_areas=[]
                )
            
            # Calculate dominant emotions
            emotion_counts = {}
            mood_scores = []
            stress_levels = []
            
            for emotion in emotions:
                emotion_counts[emotion.primary_emotion] = emotion_counts.get(emotion.primary_emotion, 0) + 1
                mood_scores.append(emotion.mood_score)
                stress_levels.append(emotion.stress_level)
            
            dominant_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
            dominant_emotions = [emotion[0] for emotion in dominant_emotions[:3]]
            
            # Calculate average mood
            average_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0.0
            
            # Calculate mood stability (lower variance = more stable)
            if len(mood_scores) > 1:
                mood_variance = sum((score - average_mood) ** 2 for score in mood_scores) / len(mood_scores)
                mood_stability = max(0.0, 1.0 - mood_variance)
            else:
                mood_stability = 1.0
            
            # Analyze stress patterns
            average_stress = sum(stress_levels) / len(stress_levels) if stress_levels else 0.0
            stress_patterns = []
            
            if average_stress > 0.7:
                stress_patterns.append("高ストレス状態")
            elif average_stress > 0.4:
                stress_patterns.append("中程度のストレス")
            else:
                stress_patterns.append("低ストレス状態")
            
            # Generate improvement areas
            improvement_areas = []
            if average_mood < -0.2:
                improvement_areas.append("気分の向上")
            if average_stress > 0.6:
                improvement_areas.append("ストレス管理")
            if mood_stability < 0.5:
                improvement_areas.append("感情の安定性")
            
            return EmotionTrend(
                timeframe=timeframe,
                dominant_emotions=dominant_emotions,
                average_mood=average_mood,
                mood_stability=mood_stability,
                stress_patterns=stress_patterns,
                improvement_areas=improvement_areas
            )
            
        except Exception as e:
            logger.error(f"Error analyzing emotion trends: {e}")
            return EmotionTrend(
                timeframe=timeframe,
                dominant_emotions=["エラー"],
                average_mood=0.0,
                mood_stability=0.0,
                stress_patterns=[],
                improvement_areas=[]
            )

    async def get_emotional_insights(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive emotional insights"""
        try:
            recent_emotions = await self.get_emotion_history(user_id, 7)
            trends = await self.analyze_emotion_trends(user_id, "weekly")
            
            if not recent_emotions:
                return {
                    "current_state": "データ不足",
                    "recent_pattern": "分析不可",
                    "recommendations": ["まずは会話を重ねましょう"]
                }
            
            current_emotion = recent_emotions[0]
            
            # Generate recommendations
            recommendations = []
            
            if current_emotion.stress_level > 0.7:
                recommendations.append("リラックスできる時間を作ってください")
            
            if current_emotion.mood_score < -0.3:
                recommendations.append("好きなことをして気分転換をしましょう")
            
            if current_emotion.energy_level < 0.3:
                recommendations.append("十分な休息を取ることをお勧めします")
            
            if trends.average_mood > 0.5:
                recommendations.append("とても良い精神状態を保っていますね")
            
            return {
                "current_state": current_emotion.primary_emotion,
                "current_mood_score": current_emotion.mood_score,
                "current_stress": current_emotion.stress_level,
                "current_energy": current_emotion.energy_level,
                "recent_pattern": f"過去7日間の主な感情: {', '.join(trends.dominant_emotions)}",
                "average_mood": trends.average_mood,
                "mood_stability": trends.mood_stability,
                "recommendations": recommendations if recommendations else ["今の調子を維持してください"]
            }
            
        except Exception as e:
            logger.error(f"Error getting emotional insights: {e}")
            return {
                "current_state": "エラー",
                "recent_pattern": "分析エラー",
                "recommendations": ["システムエラーが発生しました"]
            }

    async def _save_emotion_state(self, user_id: int, emotion_state: EmotionState):
        """Save emotion state to file"""
        try:
            emotion_file = os.path.join(self.emotion_data_dir, f"user_{user_id}.json")
            
            # Load existing data
            if os.path.exists(emotion_file):
                with open(emotion_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"user_id": user_id, "emotions": []}
            
            # Add new emotion state
            emotion_dict = {
                "timestamp": emotion_state.timestamp.isoformat(),
                "primary_emotion": emotion_state.primary_emotion,
                "emotion_intensity": emotion_state.emotion_intensity,
                "secondary_emotions": emotion_state.secondary_emotions,
                "mood_score": emotion_state.mood_score,
                "stress_level": emotion_state.stress_level,
                "energy_level": emotion_state.energy_level,
                "context": emotion_state.context,
                "triggers": emotion_state.triggers
            }
            
            data["emotions"].append(emotion_dict)
            
            # Keep only last 100 emotion states
            if len(data["emotions"]) > 100:
                data["emotions"] = data["emotions"][-100:]
            
            # Save to file
            with open(emotion_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Emotion state saved for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving emotion state: {e}")

    def generate_empathetic_response_context(self, emotion_state: EmotionState) -> str:
        """Generate context for empathetic AI responses"""
        context_parts = []
        
        # Add emotion awareness
        if emotion_state.primary_emotion in ["悲しい", "不安", "疲労"]:
            context_parts.append("ユーザーは少し落ち込んでいるようです。温かく励ますような応答を心がけてください。")
        elif emotion_state.primary_emotion in ["喜び", "興奮", "幸せ"]:
            context_parts.append("ユーザーは良い気分のようです。その喜びを共有し、さらに盛り上げてください。")
        elif emotion_state.stress_level > 0.7:
            context_parts.append("ユーザーはストレスを感じているようです。落ち着いた tone で支援的な応答をしてください。")
        
        # Add energy level awareness
        if emotion_state.energy_level < 0.3:
            context_parts.append("ユーザーは疲れているようです。シンプルで理解しやすい応答を心がけてください。")
        elif emotion_state.energy_level > 0.7:
            context_parts.append("ユーザーは元気で活発なようです。エネルギッシュな応答で応えてください。")
        
        return " ".join(context_parts) if context_parts else "通常の親しみやすい応答でお願いします。"