"""
Nickname Generator - Advanced nickname suggestion system
"""
import json
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NicknameGenerator:
    """Generates personalized nicknames based on user profiles and preferences"""
    
    def __init__(self):
        self.nickname_patterns = {
            # 基本パターン
            "suffix_patterns": ["ちゃん", "くん", "さん", "たん", "にゃん", "ぴょん", "りん"],
            "prefix_patterns": ["お", "み", "小", "ちび", "可愛い"],
            
            # 性格別パターン
            "friendly_patterns": ["ちゃん", "くん", "たん", "ぴょん"],
            "formal_patterns": ["さん", "様", "殿"],
            "cute_patterns": ["たん", "にゃん", "ぴょん", "りん", "ちび"],
            "cool_patterns": ["", "さん", "君"],
            
            # 特殊パターン
            "gaming_patterns": ["ゲーマー", "プレイヤー", "マスター", "王", "姫"],
            "tech_patterns": ["エンジニア", "ハッカー", "コーダー", "マスター", "博士"],
            "creative_patterns": ["アーティスト", "クリエイター", "マエストロ", "天才", "魔法使い"],
            
            # 関係性別パターン
            "family_patterns": ["お兄ちゃん", "お姉ちゃん", "パパ", "ママ", "兄", "姉"],
            "friend_patterns": ["ちゃん", "くん", "たん", "相棒", "バディ"],
            "close_patterns": ["ダーリン", "ハニー", "愛しい人", "運命の人", "大切な人"],
            "respect_patterns": ["先生", "師匠", "先輩", "マスター", "様"]
        }
        
        # 音韻変化パターン
        self.sound_variations = {
            "あ": ["あ", "あー", "あん"],
            "い": ["い", "いー", "ちゃん"],
            "う": ["う", "うー", "ぴょん"],
            "え": ["え", "えー", "たん"],
            "お": ["お", "おー", "にゃん"],
            "か": ["か", "かー", "きゃん"],
            "き": ["き", "きー", "っち"],
            "く": ["く", "くー", "っくん"],
            "け": ["け", "けー", "っけ"],
            "こ": ["こ", "こー", "っこ"],
            "ん": ["ん", "んちゃん", "んたん"]
        }
    
    def generate_nicknames(self, user_profile: Dict[str, Any], user_name: str, 
                          relationship_level: str = "friend", count: int = 8) -> List[Dict[str, str]]:
        """Generate personalized nicknames based on user profile"""
        try:
            nicknames = []
            
            # 1. 名前ベースのニックネーム
            name_based = self._generate_name_based_nicknames(user_name, relationship_level)
            nicknames.extend(name_based)
            
            # 2. 性格ベースのニックネーム
            personality_based = self._generate_personality_based_nicknames(user_profile, user_name)
            nicknames.extend(personality_based)
            
            # 3. 興味・趣味ベースのニックネーム
            interest_based = self._generate_interest_based_nicknames(user_profile, user_name)
            nicknames.extend(interest_based)
            
            # 4. 関係性ベースのニックネーム
            relationship_based = self._generate_relationship_based_nicknames(user_name, relationship_level)
            nicknames.extend(relationship_based)
            
            # 5. 特殊パターンのニックネーム
            special_based = self._generate_special_pattern_nicknames(user_profile, user_name)
            nicknames.extend(special_based)
            
            # 重複除去と選択
            unique_nicknames = self._remove_duplicates(nicknames)
            
            # スコアリングして上位を選択
            scored_nicknames = self._score_nicknames(unique_nicknames, user_profile, relationship_level)
            
            return scored_nicknames[:count]
            
        except Exception as e:
            logger.error(f"Error generating nicknames: {e}")
            # フォールバック：基本的なニックネーム
            return self._generate_fallback_nicknames(user_name)
    
    def _generate_name_based_nicknames(self, name: str, relationship_level: str) -> List[Dict[str, str]]:
        """名前に基づくニックネーム生成"""
        nicknames = []
        
        # 名前の短縮形
        if len(name) > 2:
            short_name = name[:2]
            nicknames.append({
                "nickname": short_name,
                "reason": f"{name}の短縮形",
                "type": "name_shortening",
                "formality": "casual"
            })
        
        # 最初の文字 + suffix
        first_char = name[0] if name else "名前"
        for suffix in self._get_suffix_by_relationship(relationship_level):
            nicknames.append({
                "nickname": first_char + suffix,
                "reason": f"{name}の最初の文字に{suffix}を付けて親しみやすく",
                "type": "first_char_suffix",
                "formality": "casual"
            })
        
        # 名前の反復
        if len(name) >= 1:
            repeated = name[0] + name[0]
            nicknames.append({
                "nickname": repeated + "ちゃん",
                "reason": f"{name}の文字を繰り返して可愛らしく",
                "type": "repetition",
                "formality": "cute"
            })
        
        return nicknames
    
    def _generate_personality_based_nicknames(self, profile: Dict[str, Any], name: str) -> List[Dict[str, str]]:
        """性格特性に基づくニックネーム生成"""
        nicknames = []
        traits = profile.get("personality_traits", [])
        
        trait_mapping = {
            "優しい": ["優しい子", "天使", "癒し系"],
            "明るい": ["太陽", "光", "ポジティブ"],
            "面白い": ["お笑い", "ムードメーカー", "エンターテイナー"],
            "真面目": ["しっかり者", "頼れる人", "リーダー"],
            "創造的": ["アーティスト", "クリエイター", "発明家"],
            "知的": ["博士", "先生", "賢者"],
            "活発": ["エネルギッシュ", "アクティブ", "元気っ子"],
            "冷静": ["クール", "落ち着いた人", "大人"],
            "協力的": ["チームワーカー", "サポーター", "パートナー"],
            "探究心旺盛": ["探検家", "研究者", "好奇心"]
        }
        
        for trait in traits:
            if trait in trait_mapping:
                for suggestion in trait_mapping[trait]:
                    nicknames.append({
                        "nickname": suggestion,
                        "reason": f"{trait}な性格から連想",
                        "type": "personality",
                        "formality": "descriptive"
                    })
        
        return nicknames
    
    def _generate_interest_based_nicknames(self, profile: Dict[str, Any], name: str) -> List[Dict[str, str]]:
        """興味・趣味に基づくニックネーム生成"""
        nicknames = []
        interests = profile.get("interests", [])
        
        interest_mapping = {
            "ゲーム": ["ゲーマー", "プレイヤー", "ゲーム王", "ゲーム姫"],
            "プログラミング": ["コーダー", "ハッカー", "エンジニア", "デベロッパー"],
            "音楽": ["ミュージシャン", "音楽家", "メロディー", "リズム"],
            "アニメ": ["オタク", "アニメ好き", "2次元", "萌え"],
            "読書": ["本虫", "読書家", "文学少女", "知識人"],
            "料理": ["シェフ", "料理人", "グルメ", "美食家"],
            "スポーツ": ["アスリート", "スポーツマン", "活動家", "体育会系"],
            "映画": ["映画通", "シネマ", "映像", "ドラマ"],
            "旅行": ["トラベラー", "冒険家", "旅人", "探検家"],
            "写真": ["フォトグラファー", "カメラマン", "芸術家", "アーティスト"]
        }
        
        for interest in interests:
            if interest in interest_mapping:
                for suggestion in interest_mapping[interest]:
                    nicknames.append({
                        "nickname": suggestion,
                        "reason": f"{interest}への興味から",
                        "type": "interest",
                        "formality": "descriptive"
                    })
        
        return nicknames
    
    def _generate_relationship_based_nicknames(self, name: str, relationship_level: str) -> List[Dict[str, str]]:
        """関係性レベルに基づくニックネーム生成"""
        nicknames = []
        
        relationship_patterns = {
            "stranger": ["さん", "様"],
            "friend": ["ちゃん", "くん", "君"],
            "close": ["たん", "ぴょん", "にゃん"],
            "best_friend": ["相棒", "バディ", "親友"],
            "family": ["お兄ちゃん", "お姉ちゃん", "家族"],
            "intimate": ["ダーリン", "ハニー", "愛しい人"],
            "soulmate": ["運命の人", "大切な人", "永遠の人"]
        }
        
        patterns = relationship_patterns.get(relationship_level, ["ちゃん", "くん"])
        
        for pattern in patterns:
            if pattern in ["ちゃん", "くん", "さん", "様", "たん", "ぴょん", "にゃん"]:
                nickname = (name[0] if name else "君") + pattern
            else:
                nickname = pattern
            
            nicknames.append({
                "nickname": nickname,
                "reason": f"{relationship_level}関係に適した呼び方",
                "type": "relationship",
                "formality": self._get_formality_level(relationship_level)
            })
        
        return nicknames
    
    def _generate_special_pattern_nicknames(self, profile: Dict[str, Any], name: str) -> List[Dict[str, str]]:
        """特殊パターンのニックネーム生成"""
        nicknames = []
        
        # カスタム属性に基づく特殊パターン
        custom_attrs = profile.get("custom_attributes", {})
        
        # プログラミング関連
        if any("プログラム" in str(v) or "コード" in str(v) for v in custom_attrs.values()):
            tech_names = ["コードマスター", "デバッガー", "アルゴリズム", "バイナリ"]
            for tech_name in tech_names:
                nicknames.append({
                    "nickname": tech_name,
                    "reason": "プログラミングスキルから",
                    "type": "special_tech",
                    "formality": "cool"
                })
        
        # 時間帯に基づく
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            nicknames.append({
                "nickname": "朝の人",
                "reason": "朝の時間帯によく活動",
                "type": "time_based",
                "formality": "casual"
            })
        elif 18 <= current_hour < 24:
            nicknames.append({
                "nickname": "夜型",
                "reason": "夜の時間帯によく活動",
                "type": "time_based",
                "formality": "casual"
            })
        
        # 音韻変化パターン
        if name and len(name) > 0:
            sound_variants = self._create_sound_variations(name)
            for variant in sound_variants[:3]:  # 最大3個
                nicknames.append({
                    "nickname": variant,
                    "reason": f"{name}の音韻変化",
                    "type": "sound_variation",
                    "formality": "cute"
                })
        
        return nicknames
    
    def _create_sound_variations(self, name: str) -> List[str]:
        """音韻変化パターンの生成"""
        variations = []
        
        if len(name) >= 1:
            first_char = name[0]
            # カタカナ変換やひらがな変換は簡単な例
            variations.append(first_char + "っち")
            variations.append(first_char + "にゃん")
            variations.append(first_char + "ぴょん")
        
        return variations
    
    def _get_suffix_by_relationship(self, relationship_level: str) -> List[str]:
        """関係性レベルに応じた適切なsuffixを取得"""
        relationship_suffixes = {
            "stranger": ["さん"],
            "friend": ["ちゃん", "くん"],
            "close": ["ちゃん", "たん", "ぴょん"],
            "best_friend": ["ちゃん", "たん", "にゃん"],
            "family": ["ちゃん", "くん"],
            "intimate": ["たん", "にゃん", "ぴょん"],
            "soulmate": ["たん", "にゃん", "ダーリン"]
        }
        
        return relationship_suffixes.get(relationship_level, ["ちゃん", "くん"])
    
    def _get_formality_level(self, relationship_level: str) -> str:
        """関係性レベルから敬語度を判定"""
        formality_map = {
            "stranger": "formal",
            "friend": "casual",
            "close": "cute",
            "best_friend": "casual",
            "family": "casual",
            "intimate": "cute",
            "soulmate": "intimate"
        }
        
        return formality_map.get(relationship_level, "casual")
    
    def _score_nicknames(self, nicknames: List[Dict[str, str]], profile: Dict[str, Any], 
                        relationship_level: str) -> List[Dict[str, str]]:
        """ニックネームをスコアリングして適切性を評価"""
        
        for nickname_data in nicknames:
            score = 0
            
            # 基本スコア
            score += 10
            
            # 関係性適合度
            if nickname_data.get("type") == "relationship":
                score += 20
            
            # 個性的要素
            if nickname_data.get("type") in ["personality", "interest"]:
                score += 15
            
            # 名前ベース
            if nickname_data.get("type").startswith("name"):
                score += 12
            
            # 可愛らしさ（関係性によって調整）
            if nickname_data.get("formality") == "cute" and relationship_level in ["close", "intimate"]:
                score += 18
            elif nickname_data.get("formality") == "formal" and relationship_level == "stranger":
                score += 15
            
            # 長さによる調整
            nickname_len = len(nickname_data.get("nickname", ""))
            if 2 <= nickname_len <= 6:
                score += 10
            elif nickname_len > 8:
                score -= 5
            
            # ランダム要素（多様性のため）
            score += random.randint(0, 5)
            
            nickname_data["score"] = score
        
        # スコア順にソート
        return sorted(nicknames, key=lambda x: x.get("score", 0), reverse=True)
    
    def _remove_duplicates(self, nicknames: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """重複するニックネームを除去"""
        seen = set()
        unique_nicknames = []
        
        for nickname_data in nicknames:
            nickname = nickname_data.get("nickname", "")
            if nickname and nickname not in seen:
                seen.add(nickname)
                unique_nicknames.append(nickname_data)
        
        return unique_nicknames
    
    def _generate_fallback_nicknames(self, name: str) -> List[Dict[str, str]]:
        """フォールバック用の基本的なニックネーム"""
        return [
            {
                "nickname": f"{name}ちゃん",
                "reason": "親しみやすい基本的な呼び方",
                "type": "fallback",
                "formality": "casual",
                "score": 10
            },
            {
                "nickname": f"{name}くん",
                "reason": "フレンドリーな基本的な呼び方",
                "type": "fallback",
                "formality": "casual",
                "score": 10
            }
        ]

# Global instance
nickname_generator = NicknameGenerator()