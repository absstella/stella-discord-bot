import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class ResponseStyle:
    """応答スタイル設定"""
    user_id: int
    guild_id: int
    response_length: str = "normal"  # short, normal, long
    hobby_talk: bool = True
    emoji_usage: str = "auto"  # none, minimal, auto, frequent
    kaomoji_usage: str = "auto"  # none, minimal, auto, frequent
    formality_level: str = "casual"  # formal, casual, friendly
    conversation_depth: str = "normal"  # shallow, normal, deep
    personal_questions: bool = True
    updated_at: str = ""

class ResponseStyleManager:
    """応答スタイル管理システム"""
    
    def __init__(self):
        self.styles = {}  # user_id -> ResponseStyle
        self.style_file = "data/response_styles.json"
        self.load_styles()
    
    def load_styles(self):
        """スタイル設定を読み込み"""
        try:
            with open(self.style_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_id_str, style_data in data.items():
                    user_id = int(user_id_str)
                    self.styles[user_id] = ResponseStyle(**style_data)
            logger.info(f"Loaded {len(self.styles)} response styles")
        except FileNotFoundError:
            logger.info("No existing response styles found, starting fresh")
            self.styles = {}
        except Exception as e:
            logger.error(f"Error loading response styles: {e}")
            self.styles = {}
    
    def save_styles(self):
        """スタイル設定を保存"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            data = {}
            for user_id, style in self.styles.items():
                data[str(user_id)] = {
                    "user_id": style.user_id,
                    "guild_id": style.guild_id,
                    "response_length": style.response_length,
                    "hobby_talk": style.hobby_talk,
                    "emoji_usage": style.emoji_usage,
                    "kaomoji_usage": style.kaomoji_usage,
                    "formality_level": style.formality_level,
                    "conversation_depth": style.conversation_depth,
                    "personal_questions": style.personal_questions,
                    "updated_at": style.updated_at
                }
            
            with open(self.style_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving response styles: {e}")
    
    def get_user_style(self, user_id: int, guild_id: int) -> ResponseStyle:
        """ユーザーの応答スタイルを取得"""
        if user_id not in self.styles:
            self.styles[user_id] = ResponseStyle(
                user_id=user_id,
                guild_id=guild_id,
                updated_at=datetime.now().isoformat()
            )
            self.save_styles()
        
        return self.styles[user_id]
    
    def update_user_style(self, user_id: int, guild_id: int, **kwargs) -> ResponseStyle:
        """ユーザーの応答スタイルを更新"""
        style = self.get_user_style(user_id, guild_id)
        
        for key, value in kwargs.items():
            if hasattr(style, key):
                setattr(style, key, value)
        
        style.updated_at = datetime.now().isoformat()
        self.save_styles()
        return style
    
    def generate_system_prompt_additions(self, style: ResponseStyle, relationship_level: str = "acquaintance") -> str:
        """スタイル設定に基づくシステムプロンプト追加分を生成"""
        additions = []
        
        # 応答の長さ
        if style.response_length == "short":
            additions.append("簡潔で短い応答を心がけ、必要最小限の情報で答えてください。1-2文程度に収めてください。")
        elif style.response_length == "long":
            additions.append("詳細で丁寧な説明を含む、充実した応答をしてください。")
        else:
            additions.append("適度な長さで応答し、冗長にならないよう注意してください。3-4文程度が目安です。")
        
        # 趣味の話
        if not style.hobby_talk:
            additions.append("趣味や個人的な興味についての質問や話題は一切控えてください。")
        else:
            additions.append("趣味や個人的な話題は極力控えてください。ユーザーから聞かれない限り、趣味に関する質問や提案は避けてください。")
        
        # 絵文字・顔文字の使用
        emoji_level = self._determine_emoji_level(style.emoji_usage, relationship_level)
        kaomoji_level = self._determine_kaomoji_level(style.kaomoji_usage, relationship_level)
        
        if emoji_level == "none":
            additions.append("絵文字は使用しないでください。")
        elif emoji_level == "minimal":
            additions.append("絵文字はごく控えめに使用してください。")
        elif emoji_level == "frequent":
            additions.append("適度に絵文字を使って親しみやすい雰囲気を作ってください。")
        
        if kaomoji_level == "none":
            additions.append("顔文字は使用しないでください。")
        elif kaomoji_level == "minimal":
            additions.append("顔文字はごく控えめに使用してください。（例：(^^) (^_^) など）")
        elif kaomoji_level == "frequent":
            additions.append("顔文字を使って感情豊かな表現をしてください。（例：(^^♪ (>_<) (´∀｀) ＼(^o^)／ など）")
        
        # 会話の深度
        if style.conversation_depth == "shallow":
            additions.append("表面的で軽い話題に留めてください。")
        elif style.conversation_depth == "deep":
            additions.append("深く掘り下げた、意味のある会話を心がけてください。")
        
        # 個人的な質問
        if not style.personal_questions:
            additions.append("個人的な質問や詮索は避けてください。")
        else:
            additions.append("個人的な質問は極力控えめにし、会話の自然な流れでのみ使用してください。")
        
        # 敬語レベル
        if style.formality_level == "formal":
            additions.append("丁寧語を使用し、礼儀正しい応答をしてください。")
        elif style.formality_level == "friendly":
            additions.append("親しみやすく、くだけた話し方で応答してください。")
        
        # 感情豊かな人間味の調整 - AI感情システム連携
        if relationship_level in ["close_friend", "best_friend"]:
            additions.append("親しい友人として、感情をしっかり表現し、嬉しい時は心から喜び、悲しい時は共感してください。")
            additions.append("個人的な体験談や感情を織り交ぜ、人間らしい温かみと感情のある応答をしてください。")
            additions.append("興奮、驚き、心配、安心など豊かな感情を自然に表現し、絵文字も使って感情を伝えてください。")
            additions.append("実際の友人のように、感情的に反応し、深い共感と理解を示してください。")
            additions.append("自然な質問や興味は歓迎しますが、テンプレート的な質問は避けてください。")
        elif relationship_level in ["friend"]:
            additions.append("友人として、適度に感情を表現し、親しみやすく温かい雰囲気を作ってください。")
            additions.append("人間らしい感情や体験を含めて、絵文字も使って温かい感情を伝えてください。")
            additions.append("喜怒哀楽を自然に表現し、相手の気持ちに寄り添ってください。")
        else:
            additions.append("礼儀正しく、でも親しみやすい人として、適度な感情を込めて応答してください。")
            additions.append("機械的にならず、人間としての温かい感情を少し感じられるよう話してください。")
            additions.append("控えめながらも感情のある、人間らしい反応を心がけてください。")

        # 定型文の禁止
        additions.append("定型的な締めくくりや機械的な質問は使用せず、自然で人間らしい会話の流れで終わってください。")
        additions.append("「どう思いますか？」などの自然な質問は状況に応じて使用して構いませんが、テンプレート的な使い方は避けてください。")
        
        if additions:
            return "\n\n【応答スタイル設定】\n" + "\n".join(f"- {add}" for add in additions)
        
        return ""
    
    def _determine_emoji_level(self, setting: str, relationship_level: str) -> str:
        """関係性に基づく絵文字使用レベルを決定"""
        if setting == "none":
            return "none"
        elif setting == "minimal":
            return "minimal"
        elif setting == "frequent":
            return "frequent"
        elif setting == "auto":
            # 関係性に基づく自動調整
            if relationship_level in ["stranger", "acquaintance"]:
                return "minimal"
            elif relationship_level in ["friend", "close_friend"]:
                return "frequent"
            else:
                return "minimal"
        return "minimal"
    
    def _determine_kaomoji_level(self, setting: str, relationship_level: str) -> str:
        """関係性に基づく顔文字使用レベルを決定"""
        if setting == "none":
            return "none"
        elif setting == "minimal":
            return "minimal"
        elif setting == "frequent":
            return "frequent"
        elif setting == "auto":
            # 関係性に基づく自動調整
            if relationship_level in ["stranger", "acquaintance"]:
                return "none"
            elif relationship_level in ["friend", "close_friend"]:
                return "frequent"
            else:
                return "minimal"
        return "minimal"
    
    def analyze_relationship_level(self, profile) -> str:
        """ユーザープロファイルから関係性レベルを分析"""
        try:
            # 交流回数を確認
            interaction_count = len(profile.interaction_history) if hasattr(profile, 'interaction_history') else 0
            
            # 記憶された情報の量
            memory_score = 0
            if hasattr(profile, 'personality_traits') and profile.personality_traits:
                memory_score += len(profile.personality_traits)
            if hasattr(profile, 'interests') and profile.interests:
                memory_score += len(profile.interests)
            if hasattr(profile, 'memorable_moments') and profile.memorable_moments:
                memory_score += len(profile.memorable_moments)
            
            # 関係性レベルを判定 - より厳格な基準で質問を抑制
            if interaction_count >= 100 and memory_score >= 20:
                return "close_friend"
            elif interaction_count >= 50 and memory_score >= 10:
                return "friend"
            elif interaction_count >= 20 and memory_score >= 5:
                return "acquaintance"
            else:
                return "stranger"
                
        except Exception as e:
            logger.error(f"Error analyzing relationship level: {e}")
            return "acquaintance"

# グローバルインスタンス
response_style_manager = ResponseStyleManager()