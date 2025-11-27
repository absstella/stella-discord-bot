from datetime import datetime, date
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json

@dataclass
class UserStats:
    """User gaming statistics model"""
    user_id: int
    wins: int = 0
    losses: int = 0
    total_kda: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_games(self) -> int:
        return self.wins + self.losses
    
    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100
    
    @property
    def average_kda(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.total_kda / self.total_games
    
    def add_win(self, kda: float = 1.0):
        """Add a win to the user's stats"""
        self.wins += 1
        self.total_kda += kda
        self.updated_at = datetime.utcnow()
    
    def add_loss(self, kda: float = 0.5):
        """Add a loss to the user's stats"""
        self.losses += 1
        self.total_kda += kda
        self.updated_at = datetime.utcnow()

@dataclass
class UserProfile:
    """Enhanced user profile and memory system for personalized interactions"""
    user_id: int
    guild_id: int
    nickname: Optional[str] = None
    description: Optional[str] = None
    personality_traits: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    favorite_games: List[str] = field(default_factory=list)
    memorable_moments: List[Dict] = field(default_factory=list)
    custom_attributes: Dict[str, str] = field(default_factory=dict)
    # Enhanced memory fields
    conversation_patterns: List[Dict] = field(default_factory=list)
    emotional_context: Dict = field(default_factory=dict)
    interaction_history: List[Dict] = field(default_factory=list)
    learned_preferences: Dict = field(default_factory=dict)
    # New fields for detailed personality modeling
    speech_patterns: Dict[str, str] = field(default_factory=dict)  # 語尾、口調等
    reaction_patterns: Dict[str, str] = field(default_factory=dict)  # 特定の話題への反応
    relationship_context: Dict[str, str] = field(default_factory=dict)  # 他ユーザーとの関係性
    behavioral_traits: List[str] = field(default_factory=list)  # 行動パターン
    communication_style: Dict[str, str] = field(default_factory=dict)  # コミュニケーションスタイル
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    auto_extracted_info: Dict = field(default_factory=dict)
    communication_styles: Dict = field(default_factory=dict)
    
    # 動的拡張可能な詳細情報フィールド
    personal_details: Dict = field(default_factory=dict)  # 個人的な詳細情報
    skills_and_abilities: Dict = field(default_factory=dict)  # スキルと能力
    work_and_education: Dict = field(default_factory=dict)  # 仕事・教育関連
    lifestyle_and_habits: Dict = field(default_factory=dict)  # ライフスタイルと習慣
    opinions_and_beliefs: Dict = field(default_factory=dict)  # 意見と信念
    social_connections: Dict = field(default_factory=dict)  # 社会的つながり
    achievements_and_goals: Dict = field(default_factory=dict)  # 成果と目標
    media_preferences: Dict = field(default_factory=dict)  # メディア・エンタメ好み
    locations_and_places: Dict = field(default_factory=dict)  # 場所・地域情報
    time_patterns: Dict = field(default_factory=dict)  # 時間パターン
    emotional_patterns: Dict = field(default_factory=dict)  # 感情パターン
    mentioned_by_others: Dict = field(default_factory=dict)  # 他者からの言及
    observed_behaviors: List[Dict] = field(default_factory=list)  # 観察された行動
    dynamic_attributes: Dict = field(default_factory=dict)  # 動的に追加される属性
    
    def add_trait(self, trait: str):
        """Add a personality trait"""
        if trait not in self.personality_traits:
            self.personality_traits.append(trait)
            self.updated_at = datetime.utcnow()
    
    def remove_trait(self, trait: str):
        """Remove a personality trait"""
        if trait in self.personality_traits:
            self.personality_traits.remove(trait)
            self.updated_at = datetime.utcnow()
    
    def update_trait(self, old_trait: str, new_trait: str):
        """Update a personality trait"""
        if old_trait in self.personality_traits:
            index = self.personality_traits.index(old_trait)
            self.personality_traits[index] = new_trait
            self.updated_at = datetime.utcnow()
    
    def manage_traits_auto(self, max_traits: int = 15):
        """Automatically manage traits by removing duplicates and limiting count"""
        # Remove duplicates while preserving order
        seen = set()
        unique_traits = []
        for trait in self.personality_traits:
            if trait not in seen:
                seen.add(trait)
                unique_traits.append(trait)
        
        # Limit to max_traits, keeping most recent
        if len(unique_traits) > max_traits:
            unique_traits = unique_traits[-max_traits:]
        
        if unique_traits != self.personality_traits:
            self.personality_traits = unique_traits
            self.updated_at = datetime.utcnow()
    
    def add_interest(self, interest: str):
        """Add an interest"""
        if interest not in self.interests:
            self.interests.append(interest)
            self.updated_at = datetime.utcnow()
    
    def remove_interest(self, interest: str):
        """Remove an interest"""
        if interest in self.interests:
            self.interests.remove(interest)
            self.updated_at = datetime.utcnow()
    
    def manage_interests_auto(self, max_interests: int = 20):
        """Automatically manage interests by removing duplicates and limiting count"""
        seen = set()
        unique_interests = []
        for interest in self.interests:
            if interest not in seen:
                seen.add(interest)
                unique_interests.append(interest)
        
        if len(unique_interests) > max_interests:
            unique_interests = unique_interests[-max_interests:]
        
        if unique_interests != self.interests:
            self.interests = unique_interests
            self.updated_at = datetime.utcnow()
    
    def add_game(self, game: str):
        """Add a favorite game"""
        if game not in self.favorite_games:
            self.favorite_games.append(game)
            self.updated_at = datetime.utcnow()
    
    def add_conversation_pattern(self, pattern_type: str, pattern_data: dict):
        """Add a conversation pattern"""
        pattern = {
            "type": pattern_type,
            "data": pattern_data,
            "timestamp": datetime.utcnow().isoformat(),
            "frequency": 1
        }
        
        # Check if similar pattern exists
        for existing in self.conversation_patterns:
            if existing.get("type") == pattern_type and existing.get("data") == pattern_data:
                existing["frequency"] += 1
                existing["timestamp"] = datetime.utcnow().isoformat()
                return
        
        self.conversation_patterns.append(pattern)
        self.updated_at = datetime.utcnow()
    
    def add_speech_pattern(self, pattern_type: str, pattern_value: str):
        """Add speech pattern like 語尾、口調"""
        self.speech_patterns[pattern_type] = pattern_value
        self.updated_at = datetime.utcnow()
    
    def add_reaction_pattern(self, topic: str, reaction: str):
        """Add reaction pattern for specific topics"""
        self.reaction_patterns[topic] = reaction
        self.updated_at = datetime.utcnow()
    
    def add_relationship(self, user_id: str, relationship: str):
        """Add relationship context with another user"""
        self.relationship_context[user_id] = relationship
        self.updated_at = datetime.utcnow()
    
    def add_behavioral_trait(self, trait: str):
        """Add behavioral trait"""
        if trait not in self.behavioral_traits:
            self.behavioral_traits.append(trait)
            self.updated_at = datetime.utcnow()
    
    def add_communication_style(self, style_type: str, style_value: str):
        """Add communication style"""
        self.communication_style[style_type] = style_value
        self.updated_at = datetime.utcnow()
    
    def update_emotional_context(self, emotion: str, intensity: float, context: str = ""):
        """Update emotional context"""
        if "current_mood" not in self.emotional_context:
            self.emotional_context["current_mood"] = {}
        
        self.emotional_context["current_mood"][emotion] = {
            "intensity": intensity,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.updated_at = datetime.utcnow()
    
    def add_interaction(self, interaction_type: str, details: dict):
        """Record interaction history"""
        interaction = {
            "type": interaction_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.interaction_history.append(interaction)
        # Keep only last 50 interactions
        if len(self.interaction_history) > 50:
            self.interaction_history = self.interaction_history[-50:]
        
        self.updated_at = datetime.utcnow()
    
    def learn_preference(self, category: str, preference: str, confidence: float = 1.0):
        """Learn user preferences"""
        if category not in self.learned_preferences:
            self.learned_preferences[category] = {}
        
        if preference in self.learned_preferences[category]:
            # Increase confidence if already exists
            self.learned_preferences[category][preference]["confidence"] = min(
                1.0, self.learned_preferences[category][preference]["confidence"] + 0.1
            )
        else:
            self.learned_preferences[category][preference] = {
                "confidence": confidence,
                "learned_at": datetime.utcnow().isoformat()
            }
        
        self.updated_at = datetime.utcnow()

    def add_moment(self, moment: str, context: str = ""):
        """Add a memorable moment"""
        moment_data = {
            "text": moment,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.memorable_moments.append(moment_data)
        # Keep only recent 50 moments
        if len(self.memorable_moments) > 50:
            self.memorable_moments.pop(0)
        self.updated_at = datetime.utcnow()
    
    def set_attribute(self, key: str, value: str):
        """Set a custom attribute"""
        self.custom_attributes[key] = value
        self.updated_at = datetime.utcnow()
    
    def add_custom_attribute(self, key: str, value: str):
        """Add a custom attribute (alias for set_attribute)"""
        self.set_attribute(key, value)
    
    def get_custom_attribute(self, key: str, default=None):
        """Get a custom attribute value"""
        return self.custom_attributes.get(key, default)
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary"""
        # Update timestamp when converting to dict (indicates data modification)
        self.updated_at = datetime.utcnow()
        
        return {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "nickname": self.nickname,
            "description": self.description,
            "personality_traits": self.personality_traits,
            "interests": self.interests,
            "favorite_games": self.favorite_games,
            "memorable_moments": self.memorable_moments,
            "custom_attributes": self.custom_attributes,
            "conversation_patterns": self.conversation_patterns,
            "emotional_context": self.emotional_context,
            "interaction_history": self.interaction_history,
            "learned_preferences": self.learned_preferences,
            "speech_patterns": self.speech_patterns,
            "reaction_patterns": self.reaction_patterns,
            "relationship_context": self.relationship_context,
            "behavioral_traits": self.behavioral_traits,
            "communication_style": self.communication_style,
            "auto_extracted_info": self.auto_extracted_info,
            "communication_styles": self.communication_styles,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    def get_memory_context(self) -> str:
        """Generate memory context for AI"""
        context_parts = []
        
        if self.nickname:
            context_parts.append(f"ニックネーム: {self.nickname}")
        
        if self.description:
            context_parts.append(f"説明: {self.description}")
        
        if self.personality_traits:
            context_parts.append(f"性格特徴: {', '.join(self.personality_traits)}")
        
        if self.interests:
            context_parts.append(f"興味: {', '.join(self.interests)}")
        
        if self.favorite_games:
            context_parts.append(f"好きなゲーム: {', '.join(self.favorite_games)}")
        
        if self.memorable_moments:
            recent_moments = self.memorable_moments[-5:]  # Last 5 moments
            moments_text = []
            for moment in recent_moments:
                if isinstance(moment, dict):
                    # Handle both 'text' and 'content' fields for backward compatibility
                    moment_text = moment.get('text') or moment.get('content') or str(moment)
                else:
                    moment_text = str(moment)
                moments_text.append(f"- {moment_text}")
            context_parts.append(f"思い出: \n{chr(10).join(moments_text)}")
        
        # Enhanced memory features
        if self.learned_preferences:
            for category, prefs in self.learned_preferences.items():
                if isinstance(prefs, dict):
                    high_confidence_prefs = [
                        pref for pref, data in prefs.items() 
                        if isinstance(data, dict) and data.get("confidence", 0) > 0.7
                    ]
                    if high_confidence_prefs:
                        context_parts.append(f"{category}: {', '.join(high_confidence_prefs)}")
                elif isinstance(prefs, list):
                    # Handle legacy list format
                    context_parts.append(f"{category}: {', '.join(str(p) for p in prefs[:3])}")
        
        if self.emotional_context and "current_mood" in self.emotional_context:
            recent_emotions = []
            for emotion, data in self.emotional_context["current_mood"].items():
                if isinstance(data, dict) and data.get("intensity", 0) > 0.5:
                    recent_emotions.append(f"{emotion}({data.get('intensity', 0):.1f})")
            if recent_emotions:
                context_parts.append(f"最近の感情: {', '.join(recent_emotions)}")
        
        if self.conversation_patterns:
            frequent_patterns = [
                p for p in self.conversation_patterns 
                if isinstance(p, dict) and p.get("frequency", 0) > 2
            ]
            if frequent_patterns:
                pattern_types = [p.get("type", "") for p in frequent_patterns[:3]]
                context_parts.append(f"会話パターン: {', '.join(pattern_types)}")
        
        if self.custom_attributes:
            # Handle special attributes with better formatting
            special_attrs = []
            other_attrs = []
            
            for k, v in self.custom_attributes.items():
                if k == 'speech_style_request':
                    special_attrs.append(f"話し方の要求: {v}")
                elif k == 'relationship_request':
                    special_attrs.append(f"関係性の要求: {v}")
                elif k == 'response_style':
                    special_attrs.append(f"返信スタイル: {v}")
                elif k == 'persona':
                    special_attrs.append(f"人格設定: {v}")
                elif k == 'relationship':
                    special_attrs.append(f"関係性: {v}")
                elif k == 'auto_response_style':
                    special_attrs.append(f"推奨返信スタイル: {v}")
                elif k == 'auto_relationship':
                    special_attrs.append(f"推定関係性: {v}")
                elif k != 'auto_learning_enabled':  # Skip this internal setting
                    other_attrs.append(f"{k}: {v}")
            
            # Add special attributes first
            if special_attrs:
                context_parts.extend(special_attrs)
            
            # Add other attributes
            if other_attrs:
                context_parts.append(f"その他: {', '.join(other_attrs)}")
        
        return "\n".join(context_parts) if context_parts else ""

@dataclass
class Birthday:
    """User birthday model"""
    user_id: int
    birth_date: date
    guild_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def days_until_birthday(self) -> int:
        """Calculate days until next birthday"""
        today = datetime.now().date()
        this_year_birthday = self.birth_date.replace(year=today.year)
        
        if this_year_birthday < today:
            # Birthday already passed this year, calculate for next year
            next_birthday = this_year_birthday.replace(year=today.year + 1)
        else:
            next_birthday = this_year_birthday
        
        return (next_birthday - today).days
    
    @property
    def is_birthday_today(self) -> bool:
        """Check if today is the user's birthday"""
        today = datetime.now().date()
        return (self.birth_date.month == today.month and 
                self.birth_date.day == today.day)

@dataclass
class Reminder:
    """User reminder model"""
    id: Optional[int] = None
    user_id: int = 0
    channel_id: int = 0
    reminder_time: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_due(self) -> bool:
        """Check if the reminder is due"""
        return datetime.utcnow() >= self.reminder_time
    
    @property
    def time_remaining(self) -> str:
        """Get human-readable time remaining"""
        if self.is_due:
            return "Overdue"
        
        delta = self.reminder_time - datetime.utcnow()
        
        if delta.days > 0:
            return f"{delta.days} day(s)"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour(s)"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute(s)"
        else:
            return f"{delta.seconds} second(s)"

@dataclass
class GuildKnowledge:
    """Guild-wide shared knowledge base model"""
    guild_id: int
    knowledge_id: str
    category: str  # "facts", "rules", "events", "culture", "references", etc.
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    contributors: List[int] = field(default_factory=list)  # User IDs who contributed
    importance_score: float = 1.0  # 1-10 scale
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    source_channel_id: Optional[int] = None
    source_message_id: Optional[int] = None
    
    def add_contributor(self, user_id: int):
        """Add a contributor to this knowledge item"""
        if user_id not in self.contributors:
            self.contributors.append(user_id)
            self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a tag to this knowledge item"""
        if tag.lower() not in [t.lower() for t in self.tags]:
            self.tags.append(tag.lower())
            self.updated_at = datetime.utcnow()
    
    def update_access_time(self):
        """Update last accessed time"""
        self.last_accessed = datetime.utcnow()

@dataclass
class GuildSettings:
    """Guild-specific settings model"""
    guild_id: int
    prefix: str = "!"
    music_channel_id: Optional[int] = None
    announcement_channel_id: Optional[int] = None
    birthday_channel_id: Optional[int] = None
    auto_delete_music_messages: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MusicHistory:
    """Music playback history model"""
    id: Optional[int] = None
    guild_id: int = 0
    user_id: int = 0
    song_title: str = ""
    song_url: str = ""
    duration: Optional[int] = None
    played_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string"""
        if not self.duration:
            return "Unknown"
        
        minutes, seconds = divmod(self.duration, 60)
        return f"{minutes}:{seconds:02d}"

@dataclass
class AIConversation:
    """AI conversation log model"""
    id: Optional[int] = None
    user_id: int = 0
    channel_id: int = 0
    guild_id: int = 0
    message_content: str = ""
    response_content: str = ""
    tokens_used: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def message_preview(self) -> str:
        """Get truncated message preview"""
        if len(self.message_content) <= 100:
            return self.message_content
        return self.message_content[:97] + "..."
    
    @property
    def response_preview(self) -> str:
        """Get truncated response preview"""
        if len(self.response_content) <= 100:
            return self.response_content
        return self.response_content[:97] + "..."

# Utility functions for database operations
class DatabaseHelpers:
    """Helper functions for common database operations"""
    
    @staticmethod
    def row_to_user_stats(row) -> Optional[UserStats]:
        """Convert database row to UserStats object"""
        if not row:
            return None
        
        return UserStats(
            user_id=row['user_id'],
            wins=row['wins'],
            losses=row['losses'],
            total_kda=row['total_kda'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    @staticmethod
    def row_to_birthday(row) -> Optional[Birthday]:
        """Convert database row to Birthday object"""
        if not row:
            return None
        
        return Birthday(
            user_id=row['user_id'],
            birth_date=row['birth_date'],
            guild_id=row['guild_id'],
            created_at=row['created_at']
        )
    
    @staticmethod
    def row_to_reminder(row) -> Optional[Reminder]:
        """Convert database row to Reminder object"""
        if not row:
            return None
        
        return Reminder(
            id=row['id'],
            user_id=row['user_id'],
            channel_id=row['channel_id'],
            reminder_time=row['reminder_time'],
            message=row['message'],
            created_at=row['created_at']
        )
    
    @staticmethod
    def row_to_guild_settings(row) -> Optional[GuildSettings]:
        """Convert database row to GuildSettings object"""
        if not row:
            return None
        
        return GuildSettings(
            guild_id=row['guild_id'],
            prefix=row['prefix'],
            music_channel_id=row['music_channel_id'],
            announcement_channel_id=row['announcement_channel_id'],
            birthday_channel_id=row['birthday_channel_id'],
            auto_delete_music_messages=row['auto_delete_music_messages'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    @staticmethod
    def row_to_music_history(row) -> Optional[MusicHistory]:
        """Convert database row to MusicHistory object"""
        if not row:
            return None
        
        return MusicHistory(
            id=row['id'],
            guild_id=row['guild_id'],
            user_id=row['user_id'],
            song_title=row['song_title'],
            song_url=row['song_url'],
            duration=row['duration'],
            played_at=row['played_at']
        )
    
    @staticmethod
    def row_to_ai_conversation(row) -> Optional[AIConversation]:
        """Convert database row to AIConversation object"""
        if not row:
            return None
        
        return AIConversation(
            id=row['id'],
            user_id=row['user_id'],
            channel_id=row['channel_id'],
            guild_id=row['guild_id'],
            message_content=row['message_content'],
            response_content=row['response_content'],
            tokens_used=row['tokens_used'],
            created_at=row['created_at']
        )
    
    @staticmethod
    def row_to_user_profile(row) -> Optional[UserProfile]:
        """Convert database row to UserProfile object"""
        if not row:
            return None
        
        # Parse JSON fields
        personality_traits = json.loads(row.get('personality_traits', '[]'))
        interests = json.loads(row.get('interests', '[]'))
        favorite_games = json.loads(row.get('favorite_games', '[]'))
        memorable_moments = json.loads(row.get('memorable_moments', '[]'))
        custom_attributes = json.loads(row.get('custom_attributes', '{}'))
        
        return UserProfile(
            user_id=row['user_id'],
            guild_id=row['guild_id'],
            nickname=row.get('nickname'),
            description=row.get('description'),
            personality_traits=personality_traits,
            interests=interests,
            favorite_games=favorite_games,
            memorable_moments=memorable_moments,
            custom_attributes=custom_attributes,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

@dataclass
class SharedMemory:
    """Shared memory between users for group experiences and relationships"""
    id: Optional[int] = None
    guild_id: int = 0
    participants: List[int] = field(default_factory=list)  # User IDs involved
    memory_type: str = ""  # "group_event", "relationship", "shared_experience", etc.
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)  # For categorization
    context_data: Dict = field(default_factory=dict)  # Additional context
    created_by: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_participant(self, user_id: int):
        """Add a participant to the shared memory"""
        if user_id not in self.participants:
            self.participants.append(user_id)
            self.updated_at = datetime.utcnow()
    
    def remove_participant(self, user_id: int):
        """Remove a participant from the shared memory"""
        if user_id in self.participants:
            self.participants.remove(user_id)
            self.updated_at = datetime.utcnow()
    
    def update_context(self, key: str, value):
        """Update context data"""
        self.context_data[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_context_summary(self) -> str:
        """Get formatted context summary"""
        parts = []
        if self.title:
            parts.append(f"タイトル: {self.title}")
        if self.description:
            parts.append(f"内容: {self.description}")
        if self.tags:
            parts.append(f"タグ: {', '.join(self.tags)}")
        
        # Add context data
        for key, value in self.context_data.items():
            if isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")
        
        return "\n".join(parts)

    @staticmethod
    def row_to_shared_memory(row) -> Optional['SharedMemory']:
        """Convert database row to SharedMemory object"""
        if not row:
            return None
        
        # Parse JSON fields
        participants = json.loads(row.get('participants', '[]'))
        tags = json.loads(row.get('tags', '[]'))
        context_data = json.loads(row.get('context_data', '{}'))
        
        return SharedMemory(
            id=row.get('id'),
            guild_id=row['guild_id'],
            participants=participants,
            memory_type=row['memory_type'],
            title=row['title'],
            description=row['description'],
            tags=tags,
            context_data=context_data,
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
