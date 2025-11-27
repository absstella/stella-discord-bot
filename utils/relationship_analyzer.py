"""
Enhanced relationship analyzer for S.T.E.L.L.A. - extracts and analyzes relationship dynamics from conversations
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RelationshipAnalyzer:
    """Advanced relationship analysis from conversation patterns"""
    
    def __init__(self):
        self.relationship_indicators = {
            "intimacy_signals": [
                "愛してる", "大好き", "愛しい", "恋人", "彼女", "彼氏", "ダーリン", "ハニー",
                "♡", "💕", "💖", "💗", "💘", "💝", "💟", "❤️", "🥰", "😘", "😍",
                "一緒にいたい", "会いたい", "抱きしめ", "キス", "愛おしい"
            ],
            "family_signals": [
                "お兄ちゃん", "お姉ちゃん", "妹", "弟", "家族", "兄弟", "姉妹",
                "パパ", "ママ", "父", "母", "親", "子", "娘", "息子",
                "おじいちゃん", "おばあちゃん", "おじさん", "おばさん"
            ],
            "friendship_signals": [
                "友達", "親友", "仲間", "相棒", "バディ", "友", "同志",
                "一緒に遊ぶ", "楽しい", "面白い", "笑う", "笑顔"
            ],
            "respect_signals": [
                "尊敬", "すごい", "かっこいい", "素晴らしい", "立派", "偉い",
                "先生", "師匠", "先輩", "上司", "リーダー", "さん", "様"
            ],
            "care_signals": [
                "心配", "大丈夫", "気をつけて", "お疲れさま", "頑張って",
                "応援", "支える", "助ける", "守る", "癒し", "優しい"
            ],
            "playful_signals": [
                "いじめる", "からかう", "いたずら", "ふざける", "遊ぶ",
                "冗談", "笑わせる", "面白がる", "楽しませる"
            ],
            "dependency_signals": [
                "頼る", "甘える", "依存", "必要", "いないと", "支え",
                "助けて", "守って", "そばにいて", "離れないで"
            ]
        }
        
        self.interaction_patterns = {
            "affectionate": ["優しく", "愛情込めて", "大切に", "丁寧に"],
            "playful": ["いたずらっぽく", "ふざけて", "楽しそうに", "遊び心で"],
            "protective": ["守るように", "心配そうに", "気遣って", "注意深く"],
            "admiring": ["尊敬して", "感心して", "憧れて", "素晴らしいと思って"],
            "dependent": ["甘えて", "頼って", "すがって", "求めて"],
            "supportive": ["応援して", "励まして", "支えて", "助けて"]
        }
    
    def analyze_relationship_from_conversation(self, user_message: str, ai_response: str, 
                                             current_relationship: Dict = None) -> Dict:
        """会話から関係性の変化と深化を分析"""
        try:
            analysis = {
                "relationship_signals": {},
                "emotional_intensity": 0.0,
                "interaction_style": [],
                "relationship_evolution": {},
                "intimacy_level": 0.0,
                "communication_patterns": {},
                "relationship_dynamics": {},
                "conversation_context": {
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Combined text for analysis
            combined_text = f"{user_message} {ai_response}".lower()
            
            # Analyze relationship signals
            for signal_type, keywords in self.relationship_indicators.items():
                signal_count = sum(1 for keyword in keywords if keyword.lower() in combined_text)
                if signal_count > 0:
                    analysis["relationship_signals"][signal_type] = signal_count
            
            # Calculate emotional intensity
            emotional_markers = ["♡", "💕", "😘", "🥰", "愛", "大好き", "嬉しい", "幸せ"]
            intensity = sum(2 if marker in combined_text else 0 for marker in emotional_markers)
            analysis["emotional_intensity"] = min(intensity / 10.0, 1.0)
            
            # Analyze interaction patterns
            for pattern_type, indicators in self.interaction_patterns.items():
                if any(indicator in combined_text for indicator in indicators):
                    analysis["interaction_style"].append(pattern_type)
            
            # Determine intimacy level progression
            intimacy_indicators = {
                "stranger": 0.0,
                "acquaintance": 0.1,
                "friend": 0.3,
                "close_friend": 0.5,
                "best_friend": 0.7,
                "intimate": 0.8,
                "soulmate": 0.9,
                "eternal_bond": 1.0
            }
            
            # Calculate current intimacy based on signals
            current_intimacy = 0.0
            if analysis["relationship_signals"].get("intimacy_signals", 0) > 0:
                current_intimacy += 0.4
            if analysis["relationship_signals"].get("family_signals", 0) > 0:
                current_intimacy += 0.3
            if analysis["relationship_signals"].get("care_signals", 0) > 0:
                current_intimacy += 0.2
            if analysis["relationship_signals"].get("dependency_signals", 0) > 0:
                current_intimacy += 0.1
            
            analysis["intimacy_level"] = min(current_intimacy, 1.0)
            
            # Analyze communication patterns
            analysis["communication_patterns"] = self._analyze_communication_style(
                user_message, ai_response
            )
            
            # Detect relationship dynamics
            analysis["relationship_dynamics"] = self._analyze_relationship_dynamics(
                user_message, ai_response, analysis["relationship_signals"]
            )
            
            # Determine relationship evolution
            if current_relationship:
                analysis["relationship_evolution"] = self._calculate_relationship_evolution(
                    current_relationship, analysis
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing relationship: {e}")
            return {}
    
    def _analyze_communication_style(self, user_message: str, ai_response: str) -> Dict:
        """コミュニケーションスタイルの分析"""
        user_lower = user_message.lower()
        ai_lower = ai_response.lower()
        
        patterns = {
            "formality_level": "casual",  # formal, polite, casual, intimate
            "emotional_expression": "moderate",  # low, moderate, high, intense
            "playfulness": "some",  # none, some, moderate, high
            "affection_display": "some",  # none, subtle, some, open, intense
            "support_seeking": False,
            "support_giving": False,
            "vulnerability_shown": False,
            "protective_behavior": False
        }
        
        # Formality analysis
        if any(word in user_lower for word in ["です", "ます", "であります"]):
            patterns["formality_level"] = "formal"
        elif any(word in user_lower for word in ["だよ", "だね", "じゃん", "～ちゃん"]):
            patterns["formality_level"] = "casual"
        elif any(word in user_lower for word in ["♡", "ダーリン", "愛しい"]):
            patterns["formality_level"] = "intimate"
        
        # Emotional expression
        emotion_count = sum(1 for char in user_message + ai_response if char in "♡💕😘🥰💖💗💘")
        if emotion_count > 5:
            patterns["emotional_expression"] = "intense"
        elif emotion_count > 2:
            patterns["emotional_expression"] = "high"
        elif emotion_count > 0:
            patterns["emotional_expression"] = "moderate"
        
        # Other patterns
        patterns["support_seeking"] = any(word in user_lower for word in ["助けて", "頼む", "お願い", "困った"])
        patterns["support_giving"] = any(word in ai_lower for word in ["応援", "支える", "大丈夫", "頑張って"])
        patterns["vulnerability_shown"] = any(word in user_lower for word in ["不安", "心配", "怖い", "悲しい"])
        patterns["protective_behavior"] = any(word in ai_lower for word in ["守る", "心配", "気をつけて"])
        
        return patterns
    
    def _analyze_relationship_dynamics(self, user_message: str, ai_response: str, signals: Dict) -> Dict:
        """関係性のダイナミクスを分析"""
        dynamics = {
            "power_balance": "equal",  # user_lead, ai_lead, equal, shifting
            "emotional_investment": "mutual",  # user_high, ai_high, mutual, low
            "interaction_initiative": "balanced",  # user_driven, ai_driven, balanced
            "conflict_resolution": "harmonious",  # avoidant, harmonious, confrontational
            "growth_direction": "deepening",  # deepening, stable, uncertain, distancing
            "relationship_health": "healthy"  # healthy, concerning, toxic, nurturing
        }
        
        user_length = len(user_message)
        ai_length = len(ai_response)
        
        # Power balance analysis
        if user_length > ai_length * 2:
            dynamics["power_balance"] = "user_lead"
        elif ai_length > user_length * 2:
            dynamics["power_balance"] = "ai_lead"
        
        # Emotional investment
        user_emotions = sum(1 for char in user_message if char in "♡💕😘🥰")
        ai_emotions = sum(1 for char in ai_response if char in "♡💕😘🥰")
        
        if user_emotions > ai_emotions * 2:
            dynamics["emotional_investment"] = "user_high"
        elif ai_emotions > user_emotions * 2:
            dynamics["emotional_investment"] = "ai_high"
        
        # Growth direction based on signals
        if signals.get("intimacy_signals", 0) > 2:
            dynamics["growth_direction"] = "deepening"
        elif signals.get("respect_signals", 0) > 0:
            dynamics["growth_direction"] = "deepening"
        
        return dynamics
    
    def _calculate_relationship_evolution(self, previous: Dict, current: Dict) -> Dict:
        """関係性の進化を計算"""
        evolution = {
            "intimacy_change": 0.0,
            "stability_score": 0.0,
            "growth_rate": 0.0,
            "evolution_direction": "stable",
            "significant_changes": []
        }
        
        # Calculate intimacy change
        prev_intimacy = previous.get("intimacy_level", 0.0)
        curr_intimacy = current.get("intimacy_level", 0.0)
        evolution["intimacy_change"] = curr_intimacy - prev_intimacy
        
        if evolution["intimacy_change"] > 0.1:
            evolution["evolution_direction"] = "growing"
            evolution["significant_changes"].append("intimacy_increase")
        elif evolution["intimacy_change"] < -0.1:
            evolution["evolution_direction"] = "declining"
            evolution["significant_changes"].append("intimacy_decrease")
        
        # Stability calculation
        prev_signals = previous.get("relationship_signals", {})
        curr_signals = current.get("relationship_signals", {})
        
        signal_consistency = 0
        for signal_type in set(list(prev_signals.keys()) + list(curr_signals.keys())):
            prev_val = prev_signals.get(signal_type, 0)
            curr_val = curr_signals.get(signal_type, 0)
            if abs(prev_val - curr_val) <= 1:  # Small change indicates stability
                signal_consistency += 1
        
        evolution["stability_score"] = signal_consistency / max(len(prev_signals) + len(curr_signals), 1)
        
        return evolution
    
    def generate_relationship_summary(self, analysis_history: List[Dict]) -> Dict:
        """関係性の総合分析サマリーを生成"""
        if not analysis_history:
            return {}
        
        summary = {
            "overall_relationship_type": "友達",
            "relationship_strength": 0.0,
            "dominant_patterns": [],
            "evolution_trend": "安定",
            "key_characteristics": [],
            "intimacy_progression": [],
            "communication_evolution": {},
            "relationship_milestones": []
        }
        
        # Analyze overall patterns
        all_signals = {}
        total_intimacy = 0
        
        for analysis in analysis_history:
            # Aggregate signals
            for signal_type, count in analysis.get("relationship_signals", {}).items():
                all_signals[signal_type] = all_signals.get(signal_type, 0) + count
            
            total_intimacy += analysis.get("intimacy_level", 0)
        
        # Determine dominant relationship type
        if all_signals.get("intimacy_signals", 0) > 5:
            summary["overall_relationship_type"] = "恋人"
        elif all_signals.get("family_signals", 0) > 3:
            summary["overall_relationship_type"] = "家族"
        elif all_signals.get("friendship_signals", 0) > 3:
            summary["overall_relationship_type"] = "親友"
        elif all_signals.get("respect_signals", 0) > 3:
            summary["overall_relationship_type"] = "師弟関係"
        
        # Calculate relationship strength
        summary["relationship_strength"] = min(total_intimacy / len(analysis_history), 1.0)
        
        # Identify dominant patterns
        sorted_signals = sorted(all_signals.items(), key=lambda x: x[1], reverse=True)
        summary["dominant_patterns"] = [signal[0] for signal in sorted_signals[:3]]
        
        # Evolution trend
        if len(analysis_history) > 1:
            recent_intimacy = sum(a.get("intimacy_level", 0) for a in analysis_history[-3:]) / min(3, len(analysis_history))
            early_intimacy = sum(a.get("intimacy_level", 0) for a in analysis_history[:3]) / min(3, len(analysis_history))
            
            if recent_intimacy > early_intimacy + 0.1:
                summary["evolution_trend"] = "深化"
            elif recent_intimacy < early_intimacy - 0.1:
                summary["evolution_trend"] = "冷却"
            else:
                summary["evolution_trend"] = "安定"
        
        return summary

# Global instance
relationship_analyzer = RelationshipAnalyzer()