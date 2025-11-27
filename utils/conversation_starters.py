"""
Personalized AI Conversation Starter Generator
Generates contextually relevant conversation starters based on user profiles and patterns
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class PersonalizedConversationStarters:
    """Generate personalized conversation starters based on user data"""
    
    def __init__(self):
        self.base_starters = {
            'casual': [
                "今日はどんな一日だった？",
                "最近何か面白いことあった？",
                "調子はどう？",
                "今何してるの？",
                "週末の予定は？"
            ],
            'technical': [
                "最近取り組んでるプロジェクトはどう？",
                "新しい技術で試してみたいものある？",
                "開発で困ってることない？",
                "最近読んだ技術記事で面白いのあった？"
            ],
            'gaming': [
                "最近何のゲームやってる？",
                "新作ゲームで気になるのある？",
                "今度一緒にゲームやらない？",
                "最近のアップデートどうだった？"
            ],
            'creative': [
                "最近何か作ってる？",
                "新しいアイデア浮かんだ？",
                "創作活動の調子はどう？",
                "インスピレーション湧いてる？"
            ],
            'social': [
                "みんなでまた集まりたいね",
                "今度イベント企画しない？",
                "最近仲間と何してる？",
                "新しいメンバーと仲良くなった？"
            ]
        }
        
        self.time_based_starters = {
            'morning': [
                "おはよう！今日もよろしく",
                "朝からお疲れ様！",
                "今日の予定はどんな感じ？",
                "朝ごはんは食べた？"
            ],
            'afternoon': [
                "お疲れ様！昼間はどうだった？",
                "午後も頑張ろう！",
                "昼休み取れてる？",
                "今日は忙しい？"
            ],
            'evening': [
                "お疲れ様でした！",
                "今日も一日頑張ったね",
                "夕飯は何にする？",
                "今夜の予定は？"
            ],
            'night': [
                "夜更かししてるの？",
                "お疲れ様！ゆっくり休んでね",
                "今日はどうだった？",
                "明日の準備はできた？"
            ]
        }
        
        self.mood_based_starters = {
            'excited': [
                "なんか楽しそうだね！何があったの？",
                "テンション高いね！いいことあった？",
                "元気いっぱいだね！",
                "今日は調子良さそう！"
            ],
            'thoughtful': [
                "何か考え事してる？",
                "深く考えてるみたいだね",
                "悩み事でもある？",
                "一人で抱え込まないでよ"
            ],
            'busy': [
                "忙しそうだね、お疲れ様",
                "手伝えることある？",
                "無理しないでね",
                "たまには休憩も大事だよ"
            ],
            'relaxed': [
                "のんびりしてる？",
                "リラックスタイムだね",
                "ゆったり過ごしてる？",
                "休日は満喫してる？"
            ]
        }
        
        self.relationship_based_starters = {
            'close_friend': [
                "久しぶり！元気だった？",
                "最近どう？変わりない？",
                "今度ゆっくり話そうよ",
                "また会えて嬉しいな"
            ],
            'new_member': [
                "こんにちは！よろしくお願いします",
                "慣れてきた？分からないことあったら聞いてね",
                "みんなとの会話は楽しんでる？",
                "何か質問あったら遠慮なく！"
            ],
            'regular': [
                "いつもありがとう！",
                "今日も来てくれてありがとう",
                "最近の調子はどう？",
                "何か新しいことある？"
            ]
        }
    
    async def generate_personalized_starters(self, profile, guild_id: int, context: Dict[str, Any] = None) -> List[str]:
        """Generate personalized conversation starters based on user profile"""
        try:
            starters = []
            
            # Get base starters based on personality traits
            if profile and hasattr(profile, 'personality_traits') and profile.personality_traits:
                if 'プロデューサー気質' in profile.personality_traits or '技術' in str(profile.personality_traits):
                    starters.extend(random.sample(self.base_starters['technical'], min(2, len(self.base_starters['technical']))))
                if 'ゲーム' in str(profile.interests) or 'ゲーミング' in str(profile.personality_traits):
                    starters.extend(random.sample(self.base_starters['gaming'], min(2, len(self.base_starters['gaming']))))
                if 'クリエイティブ' in str(profile.personality_traits) or '創作' in str(profile.interests):
                    starters.extend(random.sample(self.base_starters['creative'], min(2, len(self.base_starters['creative']))))
                if '友好的' in profile.personality_traits or '社交的' in profile.personality_traits:
                    starters.extend(random.sample(self.base_starters['social'], min(2, len(self.base_starters['social']))))
            
            # Add time-based starters
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_category = 'morning'
            elif 12 <= current_hour < 17:
                time_category = 'afternoon'
            elif 17 <= current_hour < 22:
                time_category = 'evening'
            else:
                time_category = 'night'
            
            starters.extend(random.sample(self.time_based_starters[time_category], min(2, len(self.time_based_starters[time_category]))))
            
            # Add interest-based starters
            if profile and hasattr(profile, 'interests') and profile.interests:
                interest_starters = await self._generate_interest_based_starters(profile.interests)
                starters.extend(interest_starters)
            
            # Add recent conversation context starters
            if context and 'recent_topics' in context:
                context_starters = await self._generate_context_based_starters(context['recent_topics'])
                starters.extend(context_starters)
            
            # Add mood-based starters if available
            if context and 'mood' in context:
                mood_starters = self.mood_based_starters.get(context['mood'], [])
                starters.extend(random.sample(mood_starters, min(1, len(mood_starters))))
            
            # Add relationship-based starters
            relationship_type = await self._determine_relationship_type(profile, context)
            if relationship_type in self.relationship_based_starters:
                rel_starters = self.relationship_based_starters[relationship_type]
                starters.extend(random.sample(rel_starters, min(1, len(rel_starters))))
            
            # If no specific starters, use casual ones
            if not starters:
                starters.extend(random.sample(self.base_starters['casual'], min(3, len(self.base_starters['casual']))))
            
            # Remove duplicates and limit to 5-8 starters
            unique_starters = list(dict.fromkeys(starters))
            return unique_starters[:8]
            
        except Exception as e:
            logger.error(f"Error generating personalized starters: {e}")
            # Fallback to casual starters
            return random.sample(self.base_starters['casual'], min(3, len(self.base_starters['casual'])))
    
    async def _generate_interest_based_starters(self, interests: str) -> List[str]:
        """Generate starters based on user interests"""
        starters = []
        
        interests_lower = interests.lower() if interests else ""
        
        if 'アニメ' in interests_lower or 'anime' in interests_lower:
            starters.append("最近面白いアニメ見つけた？")
            starters.append("今期のアニメで何かおすすめある？")
        
        if 'ゲーム' in interests_lower or 'game' in interests_lower:
            starters.append("新しいゲーム試してみた？")
            starters.append("最近ハマってるゲームある？")
        
        if '音楽' in interests_lower or 'music' in interests_lower:
            starters.append("最近良い音楽見つけた？")
            starters.append("新しいアーティスト発見した？")
        
        if '映画' in interests_lower or 'movie' in interests_lower:
            starters.append("最近面白い映画見た？")
            starters.append("今度映画の話聞かせて！")
        
        if 'プログラミング' in interests_lower or 'programming' in interests_lower:
            starters.append("最近何のプロジェクト作ってる？")
            starters.append("新しい言語に挑戦してる？")
        
        return starters[:2]  # Limit to 2 interest-based starters
    
    async def _generate_context_based_starters(self, recent_topics: List[str]) -> List[str]:
        """Generate starters based on recent conversation topics"""
        starters = []
        
        for topic in recent_topics[:3]:  # Check last 3 topics
            if '技術' in topic or 'プログラミング' in topic:
                starters.append("さっきの技術の話、もっと詳しく聞きたいな")
            elif 'ゲーム' in topic:
                starters.append("そのゲームの続き、どうなった？")
            elif 'プロジェクト' in topic:
                starters.append("プロジェクトの進捗はどう？")
            elif '悩み' in topic or '困' in topic:
                starters.append("あの件、解決できた？")
        
        return starters[:2]
    
    async def _determine_relationship_type(self, profile, context: Dict[str, Any] = None) -> str:
        """Determine relationship type for appropriate starters"""
        if not profile:
            return 'new_member'
        
        # Check conversation frequency
        if hasattr(profile, 'custom_attributes') and profile.custom_attributes:
            conversation_count = profile.custom_attributes.get('conversation_count', 0)
            if isinstance(conversation_count, str):
                try:
                    conversation_count = int(conversation_count)
                except:
                    conversation_count = 0
            
            if conversation_count > 50:
                return 'close_friend'
            elif conversation_count > 10:
                return 'regular'
            else:
                return 'new_member'
        
        return 'regular'
    
    async def generate_contextual_starter(self, profile, recent_messages: List[Dict], guild_context: Dict = None) -> str:
        """Generate a single, highly contextual conversation starter"""
        try:
            # Analyze recent conversation patterns
            context = await self._analyze_conversation_context(recent_messages)
            
            # Generate starters based on context
            starters = await self.generate_personalized_starters(profile, guild_context.get('guild_id', 0) if guild_context else 0, context)
            
            # Select the most appropriate starter
            if starters:
                return random.choice(starters)
            else:
                return random.choice(self.base_starters['casual'])
                
        except Exception as e:
            logger.error(f"Error generating contextual starter: {e}")
            return "元気？最近どう？"
    
    async def _analyze_conversation_context(self, recent_messages: List[Dict]) -> Dict[str, Any]:
        """Analyze recent conversation context for mood and topics"""
        context = {
            'recent_topics': [],
            'mood': 'neutral'
        }
        
        if not recent_messages:
            return context
        
        # Extract topics from recent messages
        for msg in recent_messages[-5:]:  # Analyze last 5 messages
            content = msg.get('content', '').lower()
            
            # Topic detection
            if any(word in content for word in ['技術', 'プログラミング', 'コード', '開発']):
                context['recent_topics'].append('技術')
            elif any(word in content for word in ['ゲーム', 'プレイ', 'キャラクター']):
                context['recent_topics'].append('ゲーム')
            elif any(word in content for word in ['プロジェクト', '作業', '仕事']):
                context['recent_topics'].append('プロジェクト')
            elif any(word in content for word in ['悩み', '困って', '問題']):
                context['recent_topics'].append('悩み')
            
            # Mood detection
            if any(word in content for word in ['嬉しい', '楽しい', '最高', 'やった']):
                context['mood'] = 'excited'
            elif any(word in content for word in ['忙しい', '大変', '時間がない']):
                context['mood'] = 'busy'
            elif any(word in content for word in ['考えて', '悩んで', 'どうしよう']):
                context['mood'] = 'thoughtful'
            elif any(word in content for word in ['のんびり', 'ゆっくり', 'リラックス']):
                context['mood'] = 'relaxed'
        
        return context
    
    async def get_seasonal_starters(self) -> List[str]:
        """Get season-appropriate conversation starters"""
        current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:  # Winter
            return [
                "寒いけど体調は大丈夫？",
                "冬は何して過ごしてる？",
                "温かいもの飲んでる？",
                "年末年始はどうだった？"
            ]
        elif current_month in [3, 4, 5]:  # Spring
            return [
                "春になって気分はどう？",
                "新しいことに挑戦してる？",
                "桜は見に行った？",
                "新年度の調子はどう？"
            ]
        elif current_month in [6, 7, 8]:  # Summer
            return [
                "暑いけど夏バテしてない？",
                "夏休みの予定は？",
                "水分補給忘れずにね",
                "夏らしいこと何かしてる？"
            ]
        else:  # Fall
            return [
                "秋だね、過ごしやすくなった？",
                "食欲の秋？読書の秋？",
                "紅葉は見に行った？",
                "秋の夜長、何して過ごしてる？"
            ]
    
    async def get_event_based_starters(self, guild_events: List[Dict] = None) -> List[str]:
        """Get event-based conversation starters"""
        starters = []
        
        if guild_events:
            for event in guild_events:
                event_name = event.get('name', '')
                starters.append(f"{event_name}はどうだった？")
                starters.append(f"{event_name}の感想聞かせて！")
        
        # General event starters
        starters.extend([
            "最近何かイベント参加した？",
            "今度みんなでイベントやりたいね",
            "面白いイベント情報知ってる？"
        ])
        
        return starters[:3]