"""
名前認識エンジン - メンション以外でもサーバーメンバー名を認識して自動保存
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
import discord
from database.models import UserProfile

logger = logging.getLogger(__name__)

class NameRecognitionEngine:
    """サーバーメンバーの名前を認識し、会話から情報を抽出・保存するエンジン"""
    
    def __init__(self):
        self.guild_members_cache: Dict[int, Dict[str, discord.Member]] = {}
        self.name_patterns_cache: Dict[int, List[str]] = {}
        
    async def update_guild_members(self, guild: discord.Guild):
        """ギルドメンバー情報をキャッシュに更新"""
        try:
            member_dict = {}
            name_patterns = []
            
            for member in guild.members:
                if member.bot:
                    continue
                    
                # 表示名
                display_name = member.display_name.lower()
                member_dict[display_name] = member
                name_patterns.append(display_name)
                
                # ユーザー名
                username = member.name.lower()
                member_dict[username] = member
                name_patterns.append(username)
                
                # ニックネーム（もしあれば）
                if member.nick:
                    nick = member.nick.lower()
                    member_dict[nick] = member
                    name_patterns.append(nick)
                
                # 部分マッチ用の短縮名も追加
                if len(display_name) > 3:
                    for i in range(3, len(display_name) + 1):
                        short_name = display_name[:i]
                        if short_name not in member_dict:
                            member_dict[short_name] = member
                            name_patterns.append(short_name)
            
            self.guild_members_cache[guild.id] = member_dict
            self.name_patterns_cache[guild.id] = sorted(name_patterns, key=len, reverse=True)
            
            logger.info(f"Updated member cache for guild {guild.name}: {len(member_dict)} name patterns")
            
        except Exception as e:
            logger.error(f"Error updating guild members: {e}")
    
    def detect_member_names_in_text(self, text: str, guild_id: int) -> List[Tuple[discord.Member, str, str]]:
        """テキスト内のメンバー名を検出"""
        detected_members = []
        
        if guild_id not in self.name_patterns_cache:
            return detected_members
        
        text_lower = text.lower()
        patterns = self.name_patterns_cache[guild_id]
        members_dict = self.guild_members_cache[guild_id]
        
        # 既に検出されたメンバーを追跡（重複回避）
        detected_member_ids = set()
        
        for pattern in patterns:
            if len(pattern) < 2:  # 短すぎる名前は無視
                continue
                
            # 単語境界を考慮した検索
            word_pattern = r'\b' + re.escape(pattern) + r'\b'
            matches = re.finditer(word_pattern, text_lower)
            
            for match in matches:
                member = members_dict.get(pattern)
                if member and member.id not in detected_member_ids:
                    # マッチした部分の前後のコンテキストを取得
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()
                    
                    detected_members.append((member, pattern, context))
                    detected_member_ids.add(member.id)
        
        return detected_members
    
    async def extract_information_about_member(self, text: str, member_name: str, full_text: str) -> Dict[str, any]:
        """特定のメンバーについて言及されている情報を抽出"""
        try:
            # メンバー名の前後のコンテキストを分析
            name_pos = text.lower().find(member_name.lower())
            if name_pos == -1:
                return {}
            
            # 前後50文字のコンテキストを取得
            start = max(0, name_pos - 50)
            end = min(len(text), name_pos + len(member_name) + 50)
            context = text[start:end]
            
            extracted_info = {}
            
            # 性格に関する情報
            personality_patterns = [
                r'(優しい|親切|面白い|真面目|明るい|暗い|内向的|外向的|シャイ|社交的)',
                r'(頭がいい|賢い|バカ|アホ|天才|頭脳明晰)',
                r'(面倒見がいい|世話好き|放任主義)',
                r'(リーダー|フォロワー|まとめ役|ムードメーカー)'
            ]
            
            for pattern in personality_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'personality_traits' not in extracted_info:
                        extracted_info['personality_traits'] = []
                    extracted_info['personality_traits'].extend(matches)
            
            # 興味・趣味に関する情報
            interest_patterns = [
                r'(ゲーム|アニメ|漫画|映画|音楽|読書|スポーツ|料理|旅行)が?(好き|大好き|嫌い|苦手)',
                r'(プログラミング|開発|コーディング|技術)が?(得意|好き|専門)',
                r'(絵|イラスト|デザイン|写真)を?(描く|撮る|作る|制作)'
            ]
            
            for pattern in interest_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'interests' not in extracted_info:
                        extracted_info['interests'] = []
                    for match in matches:
                        if isinstance(match, tuple):
                            interest = match[0]
                        else:
                            interest = match
                        extracted_info['interests'].append(interest)
            
            # スキル・能力に関する情報
            skill_patterns = [
                r'(プログラミング|開発|デザイン|管理|営業|企画)が?(得意|上手|専門)',
                r'(Python|JavaScript|Java|C\+\+|HTML|CSS)が?(できる|得意|専門)',
                r'(英語|中国語|韓国語|フランス語)が?(話せる|得意|ペラペラ)'
            ]
            
            for pattern in skill_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'skills' not in extracted_info:
                        extracted_info['skills'] = []
                    for match in matches:
                        if isinstance(match, tuple):
                            skill = match[0]
                        else:
                            skill = match
                        extracted_info['skills'].append(skill)
            
            # 関係性に関する情報
            relationship_patterns = [
                r'(友達|友人|親友|同僚|先輩|後輩|上司|部下)',
                r'(チームメイト|パートナー|ライバル|師匠|弟子)',
                r'(家族|兄弟|姉妹|親戚|恋人|配偶者)'
            ]
            
            for pattern in relationship_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'relationships' not in extracted_info:
                        extracted_info['relationships'] = []
                    extracted_info['relationships'].extend(matches)
            
            # 仕事・学習に関する情報
            work_patterns = [
                r'(学生|会社員|フリーランス|起業家|研究者|教師|エンジニア)',
                r'(大学|高校|専門学校|大学院)の?(学生|生徒)',
                r'(会社|企業|スタートアップ|組織)で?(働く|勤務|在籍)'
            ]
            
            for pattern in work_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'work_education' not in extracted_info:
                        extracted_info['work_education'] = []
                    for match in matches:
                        if isinstance(match, tuple):
                            work = match[0]
                        else:
                            work = match
                        extracted_info['work_education'].append(work)
            
            # 場所・地域情報
            location_patterns = [
                r'(東京|大阪|名古屋|福岡|札幌|仙台|広島|京都|神戸|横浜)に?(住んでる|在住|出身)',
                r'(関東|関西|九州|北海道|東北|中部|中国|四国)の?(人|出身|在住)',
                r'(日本|アメリカ|韓国|中国|台湾|シンガポール)の?(人|出身|在住)'
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    if 'locations' not in extracted_info:
                        extracted_info['locations'] = []
                    for match in matches:
                        if isinstance(match, tuple):
                            location = match[0]
                        else:
                            location = match
                        extracted_info['locations'].append(location)
            
            # メタ情報を追加
            if extracted_info:
                extracted_info['_meta'] = {
                    'extraction_timestamp': datetime.now().isoformat(),
                    'context': context,
                    'confidence': self._calculate_confidence(extracted_info),
                    'source': 'name_recognition_engine'
                }
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting member information: {e}")
            return {}
    
    def _calculate_confidence(self, extracted_info: Dict) -> float:
        """抽出された情報の信頼度を計算"""
        confidence = 0.0
        info_count = 0
        
        for category, items in extracted_info.items():
            if category.startswith('_'):
                continue
            if isinstance(items, list):
                info_count += len(items)
                confidence += len(items) * 0.1
        
        # 情報の種類数も考慮
        category_count = len([k for k in extracted_info.keys() if not k.startswith('_')])
        confidence += category_count * 0.1
        
        return min(1.0, confidence)
    
    async def auto_update_member_profiles(self, detected_members: List[Tuple[discord.Member, str, str]], 
                                        full_text: str, speaker_id: int, guild_id: int) -> List[Dict]:
        """検出されたメンバーのプロフィールを自動更新"""
        updates_made = []
        
        for member, matched_name, context in detected_members:
            if member.id == speaker_id:  # 自分自身への言及はスキップ
                continue
            
            try:
                # メンバーについての情報を抽出
                extracted_info = await self.extract_information_about_member(
                    context, matched_name, full_text
                )
                
                if extracted_info:
                    update_record = {
                        'member_id': member.id,
                        'member_name': member.display_name,
                        'matched_name': matched_name,
                        'extracted_info': extracted_info,
                        'timestamp': datetime.now().isoformat(),
                        'speaker_id': speaker_id
                    }
                    updates_made.append(update_record)
                    
                    logger.info(f"Auto-extracted info for {member.display_name}: {list(extracted_info.keys())}")
            
            except Exception as e:
                logger.error(f"Error updating profile for {member.display_name}: {e}")
        
        return updates_made