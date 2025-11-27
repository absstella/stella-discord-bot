"""
Emotion-based Speech Processing Module
Analyzes emotions and adjusts VOICEVOX speech parameters accordingly
"""

import logging
import re
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class EmotionSpeechProcessor:
    """Process emotions and adjust speech synthesis parameters"""
    
    def __init__(self):
        self.emotion_mapping = {
            "happy": {"speed_scale": 1.1, "pitch_scale": 1.1, "intonation_scale": 1.2},
            "excited": {"speed_scale": 1.2, "pitch_scale": 1.2, "intonation_scale": 1.3},
            "sad": {"speed_scale": 0.8, "pitch_scale": 0.9, "intonation_scale": 0.7},
            "angry": {"speed_scale": 1.1, "pitch_scale": 0.8, "intonation_scale": 1.4},
            "calm": {"speed_scale": 0.9, "pitch_scale": 1.0, "intonation_scale": 0.8},
            "surprised": {"speed_scale": 1.3, "pitch_scale": 1.3, "intonation_scale": 1.5},
            "neutral": {"speed_scale": 1.0, "pitch_scale": 1.0, "intonation_scale": 1.0},
            "thoughtful": {"speed_scale": 0.85, "pitch_scale": 0.95, "intonation_scale": 0.9},
            "playful": {"speed_scale": 1.15, "pitch_scale": 1.15, "intonation_scale": 1.25}
        }
        
        self.emotion_keywords = {
            "happy": ["嬉しい", "楽しい", "幸せ", "良かった", "素晴らしい", "最高", "♪", "(*^-^*)", "(*´ω｀*)"],
            "excited": ["すごい", "やった", "わくわく", "興奮", "テンション", "！！", "!!", "きゃー"],
            "sad": ["悲しい", "寂しい", "つらい", "残念", "がっかり", "涙", "泣", "しょんぼり"],
            "angry": ["怒", "むかつく", "イライラ", "腹立つ", "許せない", "最悪", "ふざけんな"],
            "calm": ["落ち着", "穏やか", "平和", "リラックス", "静か", "のんびり", "ゆっくり"],
            "surprised": ["びっくり", "驚", "え？", "まさか", "本当に", "信じられない", "えー"],
            "thoughtful": ["考える", "思考", "悩む", "うーん", "そうですね", "なるほど", "検討"],
            "playful": ["遊び", "冗談", "ふふ", "あはは", "くすくす", "いたずら", "からかう"]
        }
        
        logger.info("Emotion Speech Processor initialized")
    
    def detect_emotion_from_text(self, text: str) -> str:
        """
        Detect primary emotion from text content
        
        Args:
            text: Input text to analyze
            
        Returns:
            str: Detected emotion category
        """
        try:
            text_lower = text.lower()
            emotion_scores = {}
            
            # Count emotion indicators
            for emotion, keywords in self.emotion_keywords.items():
                score = 0
                for keyword in keywords:
                    score += text_lower.count(keyword.lower())
                emotion_scores[emotion] = score
            
            # Find highest scoring emotion
            max_score = max(emotion_scores.values())
            if max_score > 0:
                detected_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
                logger.debug(f"Detected emotion: {detected_emotion} (score: {max_score})")
                return detected_emotion
            
            return "neutral"
            
        except Exception as e:
            logger.error(f"Error detecting emotion: {e}")
            return "neutral"
    
    def detect_emotion_from_relationship(self, relationship_level: str) -> str:
        """
        Adjust emotion based on relationship level
        
        Args:
            relationship_level: User relationship level
            
        Returns:
            str: Emotion adjustment for relationship
        """
        try:
            relationship_emotions = {
                "親友": "happy",
                "友達": "playful", 
                "知り合い": "calm",
                "初対面": "neutral",
                "恋人": "excited",
                "家族": "happy"
            }
            
            return relationship_emotions.get(relationship_level, "neutral")
            
        except Exception as e:
            logger.error(f"Error processing relationship emotion: {e}")
            return "neutral"
    
    def get_speech_parameters(self, text: str, relationship_level: str = "知り合い") -> Dict[str, float]:
        """
        Generate VOICEVOX speech parameters based on emotion analysis
        
        Args:
            text: Text content to analyze
            relationship_level: User relationship level
            
        Returns:
            Dict with speech synthesis parameters
        """
        try:
            # Detect text-based emotion
            text_emotion = self.detect_emotion_from_text(text)
            
            # Get relationship-based emotion
            relationship_emotion = self.detect_emotion_from_relationship(relationship_level)
            
            # Combine emotions (text emotion takes priority)
            primary_emotion = text_emotion if text_emotion != "neutral" else relationship_emotion
            
            # Get base parameters
            params = self.emotion_mapping.get(primary_emotion, self.emotion_mapping["neutral"]).copy()
            
            # Adjust for text length (longer text = slower speech)
            text_length = len(text)
            if text_length > 100:
                params["speed_scale"] *= 0.9
            elif text_length > 200:
                params["speed_scale"] *= 0.8
            
            # Add relationship-based adjustments
            if relationship_level in ["親友", "恋人", "家族"]:
                params["intonation_scale"] *= 1.1  # More expressive for close relationships
            
            logger.debug(f"Generated speech parameters for '{primary_emotion}': {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error generating speech parameters: {e}")
            return self.emotion_mapping["neutral"]
    
    def enhance_text_for_speech(self, text: str, emotion: str = "neutral") -> str:
        """
        Enhance text with emotion-appropriate speech markers
        
        Args:
            text: Original text
            emotion: Target emotion
            
        Returns:
            Enhanced text for speech synthesis
        """
        try:
            enhanced_text = text
            
            # Add pauses for thoughtful content
            if emotion == "thoughtful":
                enhanced_text = re.sub(r'([。！？])', r'\1、', enhanced_text)
            
            # Speed up excited speech
            elif emotion == "excited":
                enhanced_text = re.sub(r'([！？])', r'\1', enhanced_text)
            
            # Add gentle pauses for sad content
            elif emotion == "sad":
                enhanced_text = re.sub(r'([。])', r'\1、、', enhanced_text)
            
            # Emphasize key words for happy content
            elif emotion == "happy":
                enhanced_text = re.sub(r'(すごい|素晴らしい|最高|良い)', r'、\1、', enhanced_text)
            
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Error enhancing text: {e}")
            return text

# Global instance for easy access
emotion_speech_processor = EmotionSpeechProcessor()