"""
Advanced Speech Pattern Management System
Analyzes and adapts to individual user communication styles
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)

@dataclass
class SpeechPattern:
    """個人の話し方パターン"""
    user_id: int
    guild_id: int
    
    # 基本的な話し方特徴
    formality_level: str = "casual"  # formal, casual, friendly, playful
    sentence_endings: List[str] = field(default_factory=list)  # よく使う語尾
    frequent_expressions: List[str] = field(default_factory=list)  # よく使う表現
    emoji_style: str = "moderate"  # none, minimal, moderate, heavy
    kaomoji_style: str = "moderate"  # none, minimal, moderate, heavy
    
    # 性格的特徴
    energy_level: str = "normal"  # low, normal, high, very_high
    politeness: str = "normal"  # very_polite, polite, normal, casual, rough
    humor_style: str = "normal"  # dry, playful, sarcastic, wholesome, none
    conversation_style: str = "balanced"  # listener, balanced, talkative
    
    # 特徴的な言い回し
    catchphrases: List[str] = field(default_factory=list)
    preferred_greetings: List[str] = field(default_factory=list)
    preferred_farewells: List[str] = field(default_factory=list)
    
    # 記号・絵文字パターン
    favorite_symbols: List[str] = field(default_factory=list)  # よく使う記号
    favorite_kaomoji: List[str] = field(default_factory=list)  # よく使う顔文字
    favorite_emojis: List[str] = field(default_factory=list)   # よく使う絵文字
    symbol_frequency: str = "moderate"  # none, minimal, moderate, heavy
    exclamation_style: str = "normal"   # minimal, normal, heavy
    
    # 学習データ
    analyzed_messages: int = 0
    last_updated: str = ""
    confidence_score: float = 0.0

class SpeechPatternManager:
    """話し方パターンの管理・学習システム"""
    
    def __init__(self):
        self.patterns = {}  # user_id -> SpeechPattern
        self.pattern_file = "data/speech_patterns.json"
        self.load_patterns()
    
    def load_patterns(self):
        """パターンデータを読み込み"""
        try:
            if os.path.exists(self.pattern_file):
                with open(self.pattern_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id_str, pattern_data in data.items():
                        user_id = int(user_id_str)
                        self.patterns[user_id] = SpeechPattern(**pattern_data)
                logger.info(f"Loaded {len(self.patterns)} speech patterns")
            else:
                logger.info("No existing speech patterns found")
                self.patterns = {}
        except Exception as e:
            logger.error(f"Error loading speech patterns: {e}")
            self.patterns = {}
    
    def save_patterns(self):
        """パターンデータを保存"""
        try:
            os.makedirs("data", exist_ok=True)
            
            data = {}
            for user_id, pattern in self.patterns.items():
                data[str(user_id)] = {
                    "user_id": pattern.user_id,
                    "guild_id": pattern.guild_id,
                    "formality_level": pattern.formality_level,
                    "sentence_endings": pattern.sentence_endings,
                    "frequent_expressions": pattern.frequent_expressions,
                    "emoji_style": pattern.emoji_style,
                    "kaomoji_style": pattern.kaomoji_style,
                    "energy_level": pattern.energy_level,
                    "politeness": pattern.politeness,
                    "humor_style": pattern.humor_style,
                    "conversation_style": pattern.conversation_style,
                    "catchphrases": pattern.catchphrases,
                    "preferred_greetings": pattern.preferred_greetings,
                    "preferred_farewells": pattern.preferred_farewells,
                    "favorite_symbols": pattern.favorite_symbols,
                    "favorite_kaomoji": pattern.favorite_kaomoji,
                    "favorite_emojis": pattern.favorite_emojis,
                    "symbol_frequency": pattern.symbol_frequency,
                    "exclamation_style": pattern.exclamation_style,
                    "analyzed_messages": pattern.analyzed_messages,
                    "last_updated": pattern.last_updated,
                    "confidence_score": pattern.confidence_score
                }
            
            with open(self.pattern_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving speech patterns: {e}")
    
    def get_or_create_pattern(self, user_id: int, guild_id: int) -> SpeechPattern:
        """ユーザーのパターンを取得または作成"""
        if user_id not in self.patterns:
            self.patterns[user_id] = SpeechPattern(
                user_id=user_id,
                guild_id=guild_id,
                last_updated=datetime.now().isoformat()
            )
            self.save_patterns()
        
        return self.patterns[user_id]
    
    def analyze_message(self, user_id: int, guild_id: int, message: str):
        """メッセージから話し方パターンを学習"""
        pattern = self.get_or_create_pattern(user_id, guild_id)
        
        # 語尾の分析
        sentence_endings = self._extract_sentence_endings(message)
        for ending in sentence_endings:
            if ending not in pattern.sentence_endings:
                pattern.sentence_endings.append(ending)
        
        # よく使う表現の分析
        expressions = self._extract_frequent_expressions(message)
        for expr in expressions:
            if expr not in pattern.frequent_expressions:
                pattern.frequent_expressions.append(expr)
        
        # 絵文字・顔文字・記号スタイルの分析
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message))
        kaomoji_count = len(re.findall(r'[（(][^)）]*[）)]|[><^_\-~=xX]+[><^_\-~=xX]*|[＞<＾＿ー～＝]+|[→←↑↓]|[★☆♪♫♡♥]', message))
        
        # 記号の使用パターンを分析
        symbol_count = len(re.findall(r'[!！?？…。、～・♪♫★☆※○●◎△▲▼▽◆◇□■♡♥→←↑↓]', message))
        exclamation_count = message.count('！') + message.count('!') + message.count('？') + message.count('?')
        ellipsis_count = message.count('…') + message.count('...')
        
        message_length = len(message)
        if message_length > 0:
            emoji_ratio = emoji_count / message_length * 100
            kaomoji_ratio = kaomoji_count / message_length * 100
            
            # 絵文字スタイル判定
            if emoji_ratio > 5:
                pattern.emoji_style = "heavy"
            elif emoji_ratio > 2:
                pattern.emoji_style = "moderate"
            elif emoji_ratio > 0:
                pattern.emoji_style = "minimal"
            else:
                pattern.emoji_style = "none"
            
            # 顔文字スタイル判定
            if kaomoji_ratio > 3:
                pattern.kaomoji_style = "heavy"
            elif kaomoji_ratio > 1:
                pattern.kaomoji_style = "moderate"
            elif kaomoji_ratio > 0:
                pattern.kaomoji_style = "minimal"
            else:
                pattern.kaomoji_style = "none"
        
        # 記号・感嘆符使用頻度の分析
        if exclamation_count >= 3:
            pattern.exclamation_style = "heavy"
        elif exclamation_count >= 1:
            pattern.exclamation_style = "normal"
        else:
            pattern.exclamation_style = "minimal"
        
        # 全体的な記号使用頻度
        if symbol_count > 5:
            pattern.symbol_frequency = "heavy"
        elif symbol_count > 2:
            pattern.symbol_frequency = "moderate"
        elif symbol_count > 0:
            pattern.symbol_frequency = "minimal"
        else:
            pattern.symbol_frequency = "none"
        
        # よく使う記号・顔文字・絵文字を記録
        symbols_in_msg = re.findall(r'[!！?？…。、～・♪♫★☆※○●◎△▲▼▽◆◇□■♡♥→←↑↓]', message)
        for symbol in symbols_in_msg:
            if symbol not in pattern.favorite_symbols:
                pattern.favorite_symbols.append(symbol)
                
        kaomoji_in_msg = re.findall(r'[（(][^)）]*[）)]|[><^_\-~=xX]+[><^_\-~=xX]*|[＞<＾＿ー～＝]+', message)
        for kaomoji in kaomoji_in_msg:
            if kaomoji not in pattern.favorite_kaomoji and len(kaomoji) > 1:
                pattern.favorite_kaomoji.append(kaomoji)
        
        emoji_in_msg = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message)
        for emoji in emoji_in_msg:
            if emoji not in pattern.favorite_emojis:
                pattern.favorite_emojis.append(emoji)
        
        # エネルギーレベルの分析
        energy_indicators = ['！', '!', '✨', '💪', '🔥', 'やったー', 'すげー', 'めっちゃ']
        energy_count = sum(message.count(indicator) for indicator in energy_indicators)
        
        if energy_count >= 3:
            pattern.energy_level = "very_high"
        elif energy_count >= 2:
            pattern.energy_level = "high"
        elif energy_count >= 1:
            pattern.energy_level = "normal"
        else:
            pattern.energy_level = "low"
        
        # 丁寧さレベルの分析
        polite_indicators = ['です', 'ます', 'ございます', 'いただき', 'させて', 'お疲れ様']
        casual_indicators = ['だよ', 'だね', 'じゃん', 'っす', 'やん', 'わ']
        
        polite_count = sum(message.count(indicator) for indicator in polite_indicators)
        casual_count = sum(message.count(indicator) for indicator in casual_indicators)
        
        if polite_count > casual_count * 2:
            pattern.politeness = "very_polite"
        elif polite_count > casual_count:
            pattern.politeness = "polite"
        elif casual_count > polite_count:
            pattern.politeness = "casual"
        else:
            pattern.politeness = "normal"
        
        # 統計更新
        pattern.analyzed_messages += 1
        pattern.last_updated = datetime.now().isoformat()
        pattern.confidence_score = min(1.0, pattern.analyzed_messages / 50.0)
        
        self.save_patterns()
        logger.info(f"Updated speech pattern for user {user_id}")
    
    def _extract_sentence_endings(self, message: str) -> List[str]:
        """文末パターンを抽出"""
        endings = []
        sentences = re.split(r'[。！？!?]', message)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 3:
                # 最後の2-3文字を語尾として抽出
                ending = sentence[-3:] if len(sentence) >= 3 else sentence
                if re.search(r'[だよねでしますかな]', ending):
                    endings.append(ending)
        
        return endings
    
    def _extract_frequent_expressions(self, message: str) -> List[str]:
        """よく使う表現を抽出"""
        expressions = []
        
        # 特徴的な表現パターン
        patterns = [
            r'やっぱり?',
            r'なんか',
            r'めっちゃ',
            r'すげー?',
            r'マジで?',
            r'ぶっちゃけ',
            r'正直',
            r'つまり',
            r'要するに',
            r'というか',
            r'でも',
            r'けど',
            r'しかし',
            r'ただ',
            r'ちなみに'
        ]
        
        for pattern in patterns:
            if re.search(pattern, message):
                match = re.search(pattern, message)
                if match:
                    expressions.append(match.group())
        
        return expressions
    
    def generate_speech_instructions(self, user_id: int, guild_id: int) -> str:
        """ユーザーの話し方に合わせた指示を生成"""
        pattern = self.get_or_create_pattern(user_id, guild_id)
        
        if pattern.confidence_score < 0.1:
            return ""  # 学習データが不足している場合は指示なし
        
        instructions = []
        
        # 基本的な話し方
        if pattern.formality_level == "formal":
            instructions.append("丁寧語を使用し、礼儀正しい話し方をしてください。")
        elif pattern.formality_level == "playful":
            instructions.append("親しみやすく、少し遊び心のある話し方をしてください。")
        elif pattern.formality_level == "casual":
            instructions.append("カジュアルで親しみやすい話し方をしてください。")
        
        # エネルギーレベル
        if pattern.energy_level == "very_high":
            instructions.append("とても元気で活発な話し方をしてください。")
        elif pattern.energy_level == "high":
            instructions.append("元気で明るい話し方をしてください。")
        elif pattern.energy_level == "low":
            instructions.append("落ち着いた、穏やかな話し方をしてください。")
        
        # 丁寧さレベル
        if pattern.politeness == "very_polite":
            instructions.append("とても丁寧な敬語を使用してください。")
        elif pattern.politeness == "casual":
            instructions.append("フランクで親しみやすい口調で話してください。")
        
        # 絵文字・顔文字スタイル
        if pattern.emoji_style == "heavy":
            instructions.append("絵文字を多めに使って感情豊かに表現してください。")
        elif pattern.emoji_style == "minimal":
            instructions.append("絵文字は控えめに使用してください。")
        elif pattern.emoji_style == "none":
            instructions.append("絵文字は使用しないでください。")
        
        if pattern.kaomoji_style == "heavy":
            instructions.append("顔文字を積極的に使って親しみやすく表現してください。")
        elif pattern.kaomoji_style == "minimal":
            instructions.append("顔文字は控えめに使用してください。")
        elif pattern.kaomoji_style == "none":
            instructions.append("顔文字は使用しないでください。")
        
        # 語尾パターン
        if pattern.sentence_endings and len(pattern.sentence_endings) > 0:
            common_endings = pattern.sentence_endings[:3]  # 最大3つまで
            instructions.append(f"以下の語尾を自然に使用してください: {', '.join(common_endings)}")
        
        # よく使う表現
        if pattern.frequent_expressions and len(pattern.frequent_expressions) > 0:
            common_expressions = pattern.frequent_expressions[:3]  # 最大3つまで
            instructions.append(f"以下の表現を自然に織り交ぜてください: {', '.join(common_expressions)}")
        
        # 記号・絵文字・顔文字スタイル
        if pattern.symbol_frequency == "heavy":
            instructions.append("記号を積極的に使って感情や強調を表現してください。")
        elif pattern.symbol_frequency == "minimal":
            instructions.append("記号は控えめに使用してください。")
        elif pattern.symbol_frequency == "none":
            instructions.append("記号は基本的に使用しないでください。")
        
        if pattern.exclamation_style == "heavy":
            instructions.append("感嘆符（！？）を多用して感情豊かに表現してください。")
        elif pattern.exclamation_style == "minimal":
            instructions.append("感嘆符は控えめに使用してください。")
        
        # よく使う記号・顔文字・絵文字
        if pattern.favorite_symbols:
            favorite_symbols = pattern.favorite_symbols[:5]  # 最大5つ
            instructions.append(f"これらの記号を適度に使用してください: {' '.join(favorite_symbols)}")
        
        if pattern.favorite_kaomoji:
            favorite_kaomoji = pattern.favorite_kaomoji[:3]  # 最大3つ
            instructions.append(f"これらの顔文字を時々使用してください: {' '.join(favorite_kaomoji)}")
        
        if pattern.favorite_emojis:
            favorite_emojis = pattern.favorite_emojis[:5]  # 最大5つ
            instructions.append(f"これらの絵文字を時々使用してください: {' '.join(favorite_emojis)}")
        
        if instructions:
            confidence_note = f"(学習度: {pattern.confidence_score:.0%}, {pattern.analyzed_messages}メッセージ分析済み)"
            return f"\n\n【個人別話し方調整】{confidence_note}\n" + "\n".join(f"- {inst}" for inst in instructions)
        
        return ""

# グローバルインスタンス
speech_pattern_manager = SpeechPatternManager()