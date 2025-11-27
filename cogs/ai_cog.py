import discord
from discord.ext import commands, tasks
from discord import app_commands
import google.generativeai as genai
import os
import json
import logging
from datetime import datetime, timezone
import asyncio
from typing import Dict, List, Optional
import aiohttp
import re

# Import database components
from database.models import UserProfile
from database.connection import db_manager
from utils.profile_storage import profile_storage
from utils.guild_knowledge_storage import GuildKnowledgeStorage
from utils.response_style_manager import response_style_manager
from utils.speech_pattern_manager import speech_pattern_manager
from utils.stella_profile_manager import stella_profile_manager
from utils.nickname_generator import nickname_generator
from utils.relationship_analyzer import relationship_analyzer
from utils.face_memory_storage import FaceMemoryStorage

# Setup logging
logger = logging.getLogger(__name__)

# Import intelligence systems with comprehensive fallback
try:
    from utils.mega_intelligence_orchestrator import MegaIntelligenceOrchestrator
    MEGA_INTELLIGENCE_AVAILABLE = True
    logger.info("Mega Intelligence Orchestrator imported successfully")
except ImportError as e:
    logger.warning(f"Mega Intelligence not available: {e}")
    try:
        from utils.basic_analysis import BasicMemoryProcessor, BasicConversationIntelligence
        BASIC_SYSTEMS_AVAILABLE = True
        MEGA_INTELLIGENCE_AVAILABLE = False
        logger.info("Basic intelligence systems imported as fallback")
    except ImportError as e2:
        logger.error(f"No intelligence systems available: {e2}")
        BASIC_SYSTEMS_AVAILABLE = False
        MEGA_INTELLIGENCE_AVAILABLE = False

# Import enhanced name recognition and profile expansion systems
try:
    from utils.name_recognition_engine import NameRecognitionEngine
    from utils.dynamic_profile_expander import DynamicProfileExpander
    from utils.aggressive_profile_expander import AggressiveProfileExpander
    NAME_RECOGNITION_AVAILABLE = True
    DYNAMIC_EXPANSION_AVAILABLE = True
    AGGRESSIVE_EXPANSION_AVAILABLE = True
    logger.info("Enhanced profile systems imported successfully")
except ImportError as e:
    logger.warning(f"Enhanced profile systems not available: {e}")
    NAME_RECOGNITION_AVAILABLE = False
    DYNAMIC_EXPANSION_AVAILABLE = False
    AGGRESSIVE_EXPANSION_AVAILABLE = False

# Additional systems - optional imports
try:
    from utils.web_intelligence import web_intelligence
    WEB_INTELLIGENCE_AVAILABLE = True
except ImportError:
    web_intelligence = None
    WEB_INTELLIGENCE_AVAILABLE = False

try:
    from utils.multi_model_orchestrator import multi_model_orchestrator
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    multi_model_orchestrator = None
    MULTI_MODEL_AVAILABLE = False

try:
    from utils.adaptive_learning_engine import adaptive_learning_engine
    ADAPTIVE_LEARNING_AVAILABLE = True
except ImportError:
    adaptive_learning_engine = None
    ADAPTIVE_LEARNING_AVAILABLE = False

try:
    from utils.profile_auto_updater import profile_auto_updater
    PROFILE_AUTO_UPDATER_AVAILABLE = True
except ImportError:
    profile_auto_updater = None
    PROFILE_AUTO_UPDATER_AVAILABLE = False

try:
    from utils.self_evolution import ConversationAnalyzer, ProfileEnricher, EvolutionLogger
    from utils.system_evolution import SystemEvolutionManager
    from utils.feature_generator import AutonomousFeatureManager
    SELF_EVOLUTION_AVAILABLE = True
    logger.info("Self-evolution system imported successfully")
except ImportError as e:
    logger.warning(f"Self-evolution system not available: {e}")
except ImportError as e:
    logger.warning(f"Self-evolution system not available: {e}")
    SELF_EVOLUTION_AVAILABLE = False

try:
    from utils.command_intent_analyzer import CommandIntentAnalyzer
    COMMAND_INTENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Command intent analyzer not available: {e}")
    COMMAND_INTENT_AVAILABLE = False

try:
    from utils.web_search_client import WebSearchClient
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Web search client not available: {e}")
    WEB_SEARCH_AVAILABLE = False

try:
    from utils.self_healing_manager import SelfHealingManager
    SELF_HEALING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Self-healing manager not available: {e}")
    SELF_HEALING_AVAILABLE = False

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        logger.info("Gemini model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        model = None
else:
    logger.warning("GEMINI_API_KEY not found - AI responses will be disabled")

# Color constants
SUCCESS_COLOR = 0x00ff00
ERROR_COLOR = 0xff0000
INFO_COLOR = 0x0099ff

class AICog(commands.Cog):
    """AI conversation and basic functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = getattr(bot, 'db_manager', None)
        self.model = model  # Assign global model to instance
        self.sessions = {}  # Store conversation sessions by channel_id
        self.admin_sessions = {}  # Store admin sessions {user_id: expiry_timestamp}
        
        # Initialize intelligence components
        self.intent_analyzer = None
        if COMMAND_INTENT_AVAILABLE:
            try:
                self.intent_analyzer = CommandIntentAnalyzer()
                logger.info("Command Intent Analyzer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Command Intent Analyzer: {e}")
        
        # Initialize Web Search Client
        self.web_search_client = None
        if WEB_SEARCH_AVAILABLE:
            try:
                self.web_search_client = WebSearchClient()
                logger.info("Web Search Client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Web Search Client: {e}")

        # Initialize emotion analyzer
        self.emotion_analyzer = None
        try:
            from utils.emotion_analyzer import EmotionAnalyzer
            self.emotion_analyzer = EmotionAnalyzer()
            logger.info("Emotion Analyzer initialized")
        except ImportError:
            logger.warning("Emotion Analyzer not available")
            
        self.guild_knowledge = GuildKnowledgeStorage()
        
        # Initialize self-evolution system
        if SELF_EVOLUTION_AVAILABLE:
            self.conversation_analyzer = ConversationAnalyzer()
            self.profile_enricher = ProfileEnricher()
            self.evolution_logger = EvolutionLogger()

            self.system_evolution = SystemEvolutionManager()
            self.feature_manager = AutonomousFeatureManager()
            logger.info("Self-evolution system initialized")
            # Start background evolution task
            self.evolution_task.start()
        else:
            self.conversation_analyzer = None
            self.profile_enricher = None
            self.evolution_logger = None

            self.system_evolution = None
            self.feature_manager = None
            
        # Initialize Face Memory Storage
        self.face_storage = FaceMemoryStorage()
        
        # Load evolution config
        self.evolution_config = self._load_evolution_config()
        
        # Initialize enhanced profile systems
        if NAME_RECOGNITION_AVAILABLE:
            self.name_recognition = NameRecognitionEngine()
            logger.info("Name recognition engine initialized")
        else:
            self.name_recognition = None
            
        if DYNAMIC_EXPANSION_AVAILABLE:
            self.profile_expander = DynamicProfileExpander()
            logger.info("Dynamic profile expander initialized")
        else:
            self.profile_expander = None
            
        if AGGRESSIVE_EXPANSION_AVAILABLE:
            self.aggressive_expander = AggressiveProfileExpander()
            logger.info("Aggressive profile expander initialized")
        else:
            self.aggressive_expander = None
        
        # Initialize all advanced intelligence systems
        if MEGA_INTELLIGENCE_AVAILABLE:
            self.mega_intelligence = MegaIntelligenceOrchestrator()
            self.web_intelligence = web_intelligence if WEB_INTELLIGENCE_AVAILABLE else None
            self.multi_model = multi_model_orchestrator if MULTI_MODEL_AVAILABLE else None
            self.adaptive_learning = adaptive_learning_engine if ADAPTIVE_LEARNING_AVAILABLE else None
            self.profile_updater = profile_auto_updater if PROFILE_AUTO_UPDATER_AVAILABLE else None
            self.neural_memory = None
            self.conversation_intelligence = None
            logger.info("Mega intelligence systems initialized")
        elif 'BASIC_SYSTEMS_AVAILABLE' in globals() and BASIC_SYSTEMS_AVAILABLE:
            self.mega_intelligence = None
            self.web_intelligence = None
            self.multi_model = None
            self.adaptive_learning = None
            self.profile_updater = profile_auto_updater if PROFILE_AUTO_UPDATER_AVAILABLE else None
            self.neural_memory = BasicMemoryProcessor()
            self.conversation_intelligence = BasicConversationIntelligence()
            logger.info("Basic intelligence systems initialized")
        else:
            self.mega_intelligence = None
            self.web_intelligence = None
            self.multi_model = None
            self.adaptive_learning = None
            self.profile_updater = None
            self.neural_memory = None
            self.conversation_intelligence = None
            logger.info("No intelligence systems available - using minimal functionality")
        
        # Initialize command intent analyzer
        if COMMAND_INTENT_AVAILABLE:
            # Define available commands
            available_commands = [
                # Music Commands
                {"name": "play", "description": "音楽を再生する", "args": ["query"]},
                {"name": "stop", "description": "音楽を停止する", "args": []},
                {"name": "skip", "description": "音楽をスキップする", "args": []},
                {"name": "queue", "description": "再生キューを表示する", "args": []},
                {"name": "join", "description": "ボイスチャンネルに参加する", "args": []},
                {"name": "leave", "description": "ボイスチャンネルから退出する", "args": []},
                
                # Profile Commands
                {"name": "myprofile", "description": "自分のプロフィールを表示する", "args": []},
                {"name": "profiles", "description": "サーバー内の全プロフィールを表示する", "args": []},
                
                # Knowledge Commands
                {"name": "knowledge_add", "description": "共有知識を追加する", "args": ["category", "title", "content"]},
                {"name": "knowledge_search", "description": "共有知識を検索する", "args": ["query"]},
                {"name": "knowledge_stats", "description": "共有知識の統計を表示する", "args": []},
                {"name": "knowledge_categories", "description": "共有知識のカテゴリ一覧を表示する", "args": []},
                {"name": "knowledge_help", "description": "共有知識システムのヘルプを表示する", "args": []},
                
                # Utility Commands
                {"name": "info", "description": "Botの情報を表示する", "args": []},
                {"name": "remind", "description": "リマインダーを設定する", "args": ["time", "message"]},
                {"name": "quote", "description": "メッセージを引用する", "args": ["message_id"]},
                {"name": "memo", "description": "メモを管理する（追加/一覧/削除）", "args": ["action", "content"]},
                {"name": "uptime", "description": "稼働時間を表示する", "args": []},
                
                # Web Search (New)
                {"name": "search", "description": "Web検索を行って情報を探す", "args": ["query"]},
                
                # Development & AI Commands
                {"name": "dev", "description": "新機能を作成する", "args": ["request"]},
                {"name": "load_feature", "description": "機能をロードする", "args": ["feature_name"]},
                {"name": "trigger_evolution", "description": "進化プロセスを手動実行する", "args": []},
                
                # Generated Features (Dynamic)
                {"name": "dice", "description": "サイコロを振る", "args": ["expression"]},
                {"name": "roll", "description": "サイコロを振る", "args": ["expression"]}
            ]
            self.intent_analyzer = CommandIntentAnalyzer(available_commands)
            logger.info("Command intent analyzer initialized")
        else:
            self.intent_analyzer = None
            
        # Initialize Web Search Client
        if WEB_SEARCH_AVAILABLE:
            self.web_search_client = WebSearchClient()
            logger.info("Web search client initialized")
        else:
            self.web_search_client = None
            
        # Initialize Self-Healing Manager
        if SELF_HEALING_AVAILABLE:
            self.self_healing_manager = SelfHealingManager(bot)
            logger.info("Self-healing manager initialized")
        else:
            self.self_healing_manager = None
        try:
            from utils.conversation_starters import PersonalizedConversationStarters
            self.conversation_starter_engine = PersonalizedConversationStarters()
            logger.info("Conversation starters system initialized")
        except ImportError:
            self.conversation_starter_engine = None
            logger.warning("Conversation starters system not available")
        
        # Initialize emotion analyzer
        try:
            from utils.emotion_analyzer import EmotionAnalyzer
            self.emotion_analyzer = EmotionAnalyzer()
            logger.info("Emotion Analyzer system initialized")
        except ImportError:
            self.emotion_analyzer = None
            logger.warning("Emotion analyzer system not available")
        
    async def get_user_profile(self, user_id: int, guild_id: int) -> UserProfile:
        """Get or create user profile"""
        try:
            # First try file-based storage
            profile = profile_storage.load_profile(user_id, guild_id)
            if profile:
                return profile
            
            # Create new profile if none exists
            profile = UserProfile(
                user_id=user_id,
                guild_id=guild_id,
                nickname=None,
                personality_traits=[],
                interests=[],
                favorite_games=[],
                custom_attributes={}
            )
            
            # Try database if available
            if self.db:
                try:
                    async with self.db.get_connection() as conn:
                        row = await conn.fetchrow(
                            "SELECT * FROM user_profiles WHERE user_id = $1 AND guild_id = $2",
                            user_id, guild_id
                        )
                    
                    if row:
                        # Parse JSON fields
                        import json
                        custom_attributes = json.loads(row['custom_attributes']) if row['custom_attributes'] else {}
                        
                        # Parse list fields from JSON strings
                        personality_traits = json.loads(row['personality_traits']) if row['personality_traits'] else []
                        interests = json.loads(row['interests']) if row['interests'] else []
                        favorite_games = json.loads(row['favorite_games']) if row['favorite_games'] else []
                        memorable_moments = json.loads(row['memorable_moments']) if row['memorable_moments'] else []
                        conversation_patterns = json.loads(row.get('conversation_patterns', '[]'))
                        emotional_context = json.loads(row.get('emotional_context', '{}'))
                        interaction_history = json.loads(row.get('interaction_history', '[]'))
                        learned_preferences = json.loads(row.get('learned_preferences', '{}'))
                        speech_patterns = json.loads(row.get('speech_patterns', '{}'))
                        reaction_patterns = json.loads(row.get('reaction_patterns', '{}'))
                        relationship_context = json.loads(row.get('relationship_context', '{}'))
                        behavioral_traits = json.loads(row.get('behavioral_traits', '[]'))
                        communication_style = json.loads(row.get('communication_style', '{}'))
                        
                        return UserProfile(
                            user_id=row['user_id'],
                            guild_id=row['guild_id'],
                            nickname=row['nickname'],
                            description=row.get('description'),
                            personality_traits=personality_traits,
                            interests=interests,
                            favorite_games=favorite_games,
                            memorable_moments=memorable_moments,
                            custom_attributes=custom_attributes,
                            conversation_patterns=conversation_patterns,
                            emotional_context=emotional_context,
                            interaction_history=interaction_history,
                            learned_preferences=learned_preferences,
                            speech_patterns=speech_patterns,
                            reaction_patterns=reaction_patterns,
                            relationship_context=relationship_context,
                            behavioral_traits=behavioral_traits,
                            communication_style=communication_style
                        )
                except Exception as db_error:
                    logger.warning(f"Database error in get_user_profile: {db_error}")
            
            # Save the new profile to file storage and return it
            profile_storage.save_profile(profile)
            return profile
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            # Return default profile if everything fails
            fallback_profile = UserProfile(
                user_id=user_id,
                guild_id=guild_id,
                nickname=None,
                personality_traits=[],
                interests=[],
                favorite_games=[],
                custom_attributes={}
            )
            # Save the new profile to file storage
            profile_storage.save_profile(fallback_profile)
            return fallback_profile

    async def save_user_profile(self, profile: UserProfile):
        """Save user profile to database"""
        try:
            # Always save to file-based storage first
            profile_storage.save_profile(profile)
            
            # Also try database if available
            if not self.db:
                return
            
            import json
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO user_profiles 
                    (user_id, guild_id, nickname, description, personality_traits, interests, favorite_games, 
                     memorable_moments, custom_attributes, conversation_patterns, emotional_context, 
                     interaction_history, learned_preferences, speech_patterns, reaction_patterns, 
                     relationship_context, behavioral_traits, communication_style, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, guild_id) 
                    DO UPDATE SET 
                        nickname = EXCLUDED.nickname,
                        description = EXCLUDED.description,
                        personality_traits = EXCLUDED.personality_traits,
                        interests = EXCLUDED.interests,
                        favorite_games = EXCLUDED.favorite_games,
                        memorable_moments = EXCLUDED.memorable_moments,
                        custom_attributes = EXCLUDED.custom_attributes,
                        conversation_patterns = EXCLUDED.conversation_patterns,
                        emotional_context = EXCLUDED.emotional_context,
                        interaction_history = EXCLUDED.interaction_history,
                        learned_preferences = EXCLUDED.learned_preferences,
                        speech_patterns = EXCLUDED.speech_patterns,
                        reaction_patterns = EXCLUDED.reaction_patterns,
                        relationship_context = EXCLUDED.relationship_context,
                        behavioral_traits = EXCLUDED.behavioral_traits,
                        communication_style = EXCLUDED.communication_style,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                profile.user_id, 
                profile.guild_id, 
                profile.nickname,
                profile.description,
                json.dumps(profile.personality_traits),
                json.dumps(profile.interests),
                json.dumps(profile.favorite_games),
                json.dumps(profile.memorable_moments),
                json.dumps(profile.custom_attributes),
                json.dumps(profile.conversation_patterns),
                json.dumps(profile.emotional_context),
                json.dumps(profile.interaction_history),
                json.dumps(profile.learned_preferences),
                json.dumps(profile.speech_patterns),
                json.dumps(profile.reaction_patterns),
                json.dumps(profile.relationship_context),
                json.dumps(profile.behavioral_traits),
                json.dumps(profile.communication_style)
                )
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")

    def get_session(self, channel_id: int) -> Dict:
        """Get or create conversation session for channel"""
        if channel_id not in self.sessions:
            self.sessions[channel_id] = {
                "permanent_history": [],  # Previously ended conversations
                "current_session": []     # Current ongoing conversation
            }
        return self.sessions[channel_id]

    async def add_to_session(self, channel_id: int, role: str, content: str, user_id: int = 0):
        """Add message to session with permanent history tracking"""
        session_data = self.get_session(channel_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        # Add to current session
        session_data["current_session"].append(message)
        
        # If current session gets too long, move older messages to permanent history
        if len(session_data["current_session"]) > 15:
            # Move the oldest 5 messages to permanent history
            for _ in range(5):
                if session_data["current_session"]:
                    old_message = session_data["current_session"].pop(0)
                    session_data["permanent_history"].append(old_message)
            
            # Keep only last 5 in permanent history
            if len(session_data["permanent_history"]) > 5:
                session_data["permanent_history"] = session_data["permanent_history"][-5:]

    def get_conversation_context(self, channel_id: int) -> List[Dict]:
        """Get full conversation context including permanent history"""
        session_data = self.get_session(channel_id)
        
        # Combine permanent history with current session
        full_context = []
        if "permanent_history" in session_data:
            full_context.extend(session_data["permanent_history"])
        if "current_session" in session_data:
            full_context.extend(session_data["current_session"])
        
        return full_context

    async def handle_memory_commands(self, ctx, question: str):
        """Handle memory commands within conversation"""
        import re
        
        # Pattern to match: "記憶して @user カテゴリ 情報" or "覚えて @user カテゴリ 情報"
        memory_patterns = [
            r'(?:記憶して|覚えて|remember)\s+<@!?(\d+)>\s+(\S+)\s+(.+)',
            r'(?:記憶して|覚えて|remember)\s+(\d{17,20})\s+(\S+)\s+(.+)',
            r'<@!?(\d+)>\s*(?:は|の)\s*(\S+)\s*(?:は|が)\s*(.+)(?:です|だ)',
            r'(\d{17,20})\s*(?:は|の)\s*(\S+)\s*(?:は|が)\s*(.+)(?:です|だ)',
            r'<@!?(\d+)>\s*(?:について|のこと)?\s*(\S+)\s*(?:は|が)\s*(.+)',
            r'(\d{17,20})\s*(?:について|のこと)?\s*(\S+)\s*(?:は|が)\s*(.+)',
        ]
        
        for pattern in memory_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                user_id = int(match.group(1))
                category = match.group(2)
                info = match.group(3).strip()
                
                # Get the mentioned user
                try:
                    user = await self.bot.fetch_user(user_id)
                    if not user:
                        continue
                    
                    # Store the information
                    profile = await self.get_user_profile(user.id, ctx.guild.id)
                    
                    if category in ["nickname", "ニックネーム", "名前"]:
                        profile.nickname = info
                    elif category in ["personality", "性格", "性格特性"]:
                        profile.add_trait(info)
                    elif category in ["interests", "興味", "趣味", "好み"]:
                        profile.add_interest(info)
                    elif category in ["games", "ゲーム", "好きなゲーム"]:
                        profile.add_game(info)
                    elif category in ["語尾", "口調", "話し方", "speech"]:
                        profile.add_speech_pattern("語尾", info)
                    elif category in ["反応", "リアクション", "reaction"]:
                        # Extract topic if mentioned
                        profile.add_reaction_pattern("general", info)
                    elif category in ["関係", "関係性", "relationship"]:
                        profile.add_relationship(str(ctx.author.id), info)
                    elif category in ["行動", "行動パターン", "behavior"]:
                        profile.add_behavioral_trait(info)
                    elif category in ["コミュニケーション", "話し方", "communication"]:
                        profile.add_communication_style("general", info)
                    else:
                        # Store in custom attributes
                        if not profile.custom_attributes:
                            profile.custom_attributes = {}
                        profile.custom_attributes[category] = info
                    
                    await self.save_user_profile(profile)
                    
                    # Add memory action to session
                    await self.add_to_session(ctx.channel.id, "assistant", f"{user.display_name}の{category}を記憶しました: {info}")
                    
                    await ctx.send(f"✅ {user.display_name}の{category}を記憶しました: {info}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error in memory handling: {e}")
                    await ctx.send(f"❌ 記憶処理でエラーが発生しました: {str(e)}")
                    return True

    def _load_evolution_config(self) -> Dict:
        """Load evolution configuration from file"""
        config_path = "config/evolution_config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load evolution config: {e}")
            return {}
        
        return False

    def cog_unload(self):
        """Clean up tasks when cog is unloaded"""
        if SELF_EVOLUTION_AVAILABLE and self.evolution_task.is_running():
            self.evolution_task.cancel()
            
    @tasks.loop(minutes=30)
    async def evolution_task(self):
        """Background task for system evolution and maintenance"""
        if self.system_evolution:
            try:
                await self.system_evolution.run_maintenance_cycle()
            except Exception as e:
                logger.error(f"Error in background evolution task: {e}")
    
    @evolution_task.before_loop
    async def before_evolution_task(self):
        """Wait for bot to be ready before starting evolution task"""
        await self.bot.wait_until_ready()

    @commands.command(name='ask', aliases=['ai', 'chat'])
    async def ask_ai(self, ctx, *, question: str):
        """Ask AI a question with conversation context"""
        try:
            logger.info(f"ask_ai method called for user {ctx.author.id} with question: {question}")
            
            # Check for conversational face analysis trigger
            # Triggers if image is attached AND question contains face-related keywords
            face_keywords = ['誰', '顔', 'who', 'face', 'identify', 'person', '見て']
            if ctx.message.attachments and any(k in question.lower() for k in face_keywords):
                logger.info(f"Conversational face analysis triggered by: {question}")
                await self.face_analysis(ctx)
                return
            
            # Check for system access password or active admin session
            SYSTEM_ACCESS_PASSWORD = "ore25iti5"
            is_system_access = False
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Check active session
            if ctx.author.id in self.admin_sessions:
                if current_time < self.admin_sessions[ctx.author.id]:
                    is_system_access = True
                else:
                    del self.admin_sessions[ctx.author.id]  # Expired
            
            # Check password in message
            if SYSTEM_ACCESS_PASSWORD in question:
                is_system_access = True
                # Remove password from question for processing
                question = question.replace(SYSTEM_ACCESS_PASSWORD, "").strip()
                
                # Register/Extend session (5 minutes)
                self.admin_sessions[ctx.author.id] = current_time + 300
                await ctx.send("🔐 システムアクセス権限を確認しました。管理者モードで応答します。(5分間有効)")
                
            # Add user message to session
            await self.add_to_session(ctx.channel.id, "user", question, ctx.author.id)

            # Initialize context parts list early for search integration
            context_parts = []
            
            # Automatically learn from conversation
            await self.auto_learn_from_conversation(ctx, question)
            
            # Check for command intent (Natural Language Command Execution)
            if self.intent_analyzer:
                intent = await self.intent_analyzer.analyze_intent(question)
                if intent:
                    command_name = intent["command"]
                    args = intent.get("args", [])
                    confidence = intent.get("confidence", 0)
                    
                    logger.info(f"Detected command intent: {command_name} (confidence: {confidence})")
            
            # Fallback: Check for explicit search keywords if no high-confidence command found
            # or if the command is not 'search'
            # User requested to ONLY search when "search" (検索) is explicitly mentioned
            search_keywords = ["検索", "search", "google", "ググって"]
            is_search_request = False
            
            if self.intent_analyzer and intent and intent["command"] == "search":
                is_search_request = True
                search_query = " ".join(intent.get("args", [])) if intent.get("args") else question
            elif any(keyword in question for keyword in search_keywords):
                # Simple keyword check fallback
                is_search_request = True
                # Use the whole question as query for fallback
                search_query = question
                logger.info(f"Fallback search triggered by keyword in: {question}")
            
            if is_search_request and self.web_search_client:
                # Special handling for search command to integrate with conversation
                await ctx.send(f"🔍 「{search_query}」について調べています...")
                
                try:
                    search_results = await self.web_search_client.search(search_query)
                    if search_results:
                        result_text = "\n".join([f"- {r['title']}: {r['snippet']} ({r['link']})" for r in search_results])
                        context_parts.append(f"\n【Web検索結果 ({search_query})】\n{result_text}\n\n指示: 上記の検索結果に基づいて、ユーザーの質問に答えてください。")
                    else:
                        context_parts.append(f"\n【Web検索結果】\n該当する情報が見つかりませんでした。")
                except Exception as e:
                    logger.error(f"Search failed: {e}")
                    context_parts.append(f"\n【Web検索結果】\n検索中にエラーが発生しました。")
                    
                # Continue to normal conversation generation with search results in context
                pass
            
            elif self.intent_analyzer and intent and intent["command"] != "search":
                 # Execute other commands if confidence is high enough
                 command_name = intent["command"]
                 args = intent.get("args", [])
                 
                 command = self.bot.get_command(command_name)
                 if command:
                     # Construct command string
                     if args:
                         arg_str = " ".join(args)
                         # Create a new message object with the command
                         new_content = f"{ctx.prefix}{command_name} {arg_str}"
                     else:
                         new_content = f"{ctx.prefix}{command_name}"
                         
                     ctx.message.content = new_content
                     await self.bot.process_commands(ctx.message)
                     return

            # Check for memory commands in the question
            memory_handled = await self.handle_memory_commands(ctx, question)
            if memory_handled:
                return
            
            # Check for relationship change requests first
            relationship_response = await self.handle_mention_based_user_updates(ctx, question)
            if relationship_response:
                await ctx.send(relationship_response)
                return
            
            # Enhanced conversation processing
            enhanced_response = await self.enhanced_conversation_processing(question, ctx)
            if enhanced_response:
                return
            
            # Analyze user's emotion state
            emotion_context = ""
            if self.emotion_analyzer:
                try:
                    emotion_state = await self.emotion_analyzer.analyze_emotion(
                        question, 
                        ctx.author.id,
                        {"channel_id": ctx.channel.id, "guild_id": ctx.guild.id}
                    )
                    emotion_context = self.emotion_analyzer.generate_empathetic_response_context(emotion_state)
                    self._last_emotion_state = emotion_state  # Store for speech adjustments
                    logger.info(f"Emotion analysis for user {ctx.author.id}: {emotion_state.primary_emotion} (intensity: {emotion_state.emotion_intensity})")
                except Exception as e:
                    logger.warning(f"Emotion analysis failed: {e}")
                    self._last_emotion_state = None
            
            # Get user profile for personalization
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            # Self‑evolution: analyze conversation and enrich profile
            if self.conversation_analyzer and self.profile_enricher and self.evolution_logger:
                try:
                    analysis_result = await self.conversation_analyzer.analyze_conversation(question, ctx.author.id)
                    enrichment_changes = await self.profile_enricher.enrich_profile(profile, analysis_result)
                    self.evolution_logger.log_learning_event("conversation_analysis", ctx.author.id, analysis_result)
                    self.evolution_logger.log_profile_update(ctx.author.id, enrichment_changes)
                except Exception as e:
                    logger.warning(f"Self‑evolution processing failed: {e}")
            
            # Add comprehensive user profile context
            if profile.nickname:
                context_parts.append(f"このユーザー({ctx.author.display_name})のニックネームは{profile.nickname}です。")
            
            if profile.personality_traits:
                context_parts.append(f"{ctx.author.display_name}の性格: {', '.join(profile.personality_traits)}")
                
            if profile.interests:
                context_parts.append(f"{ctx.author.display_name}の興味: {', '.join(profile.interests)}")
            
            if profile.favorite_games:
                context_parts.append(f"{ctx.author.display_name}の好きなゲーム: {', '.join(profile.favorite_games)}")
            
            # Add speech patterns
            if profile.speech_patterns:
                speech_info = []
                for pattern_type, pattern_value in profile.speech_patterns.items():
                    speech_info.append(f"{pattern_type}: {pattern_value}")
                context_parts.append(f"{ctx.author.display_name}の話し方: {', '.join(speech_info)}")
            
            # Add reaction patterns
            if profile.reaction_patterns:
                reaction_info = []
                for topic, reaction in profile.reaction_patterns.items():
                    reaction_info.append(f"{topic}への反応: {reaction}")
                context_parts.append(f"{ctx.author.display_name}の反応パターン: {', '.join(reaction_info)}")
            
            # Add behavioral traits
            if profile.behavioral_traits:
                context_parts.append(f"{ctx.author.display_name}の行動特性: {', '.join(profile.behavioral_traits)}")
            
            # Add communication style
            if profile.communication_style:
                comm_info = []
                for style_type, style_value in profile.communication_style.items():
                    comm_info.append(f"{style_type}: {style_value}")
                context_parts.append(f"{ctx.author.display_name}のコミュニケーション: {', '.join(comm_info)}")
            
            # Add memorable moments
            if profile.memorable_moments and isinstance(profile.memorable_moments, list):
                moments_str = []
                for moment in profile.memorable_moments[-3:]:
                    if isinstance(moment, str):
                        moments_str.append(moment)
                    elif isinstance(moment, dict):
                        moments_str.append(str(moment.get('content', moment)))
                if moments_str:
                    context_parts.append(f"{ctx.author.display_name}との印象深い出来事: {'; '.join(moments_str)}")
            
            # Add conversation patterns
            if profile.conversation_patterns and isinstance(profile.conversation_patterns, list):
                patterns_str = []
                for pattern in profile.conversation_patterns[-3:]:
                    if isinstance(pattern, str):
                        patterns_str.append(pattern)
                    elif isinstance(pattern, dict):
                        patterns_str.append(str(pattern.get('pattern', pattern)))
                if patterns_str:
                    context_parts.append(f"{ctx.author.display_name}との会話パターン: {'; '.join(patterns_str)}")
            
            # Add emotional context
            if profile.emotional_context and isinstance(profile.emotional_context, dict):
                emotion_info = []
                for emotion_type, context in list(profile.emotional_context.items())[:3]:
                    emotion_info.append(f"{emotion_type}: {context}")
                if emotion_info:
                    context_parts.append(f"{ctx.author.display_name}の感情的文脈: {'; '.join(emotion_info)}")
            
            # Add learned preferences
            if profile.learned_preferences and isinstance(profile.learned_preferences, dict):
                pref_info = []
                for pref_type, preference in list(profile.learned_preferences.items())[:3]:
                    pref_info.append(f"{pref_type}: {preference}")
                if pref_info:
                    context_parts.append(f"{ctx.author.display_name}の学習済み好み: {'; '.join(pref_info)}")
            
            # Add interaction history summary
            if profile.interaction_history and isinstance(profile.interaction_history, list):
                interactions_str = []
                for interaction in profile.interaction_history[-2:]:
                    if isinstance(interaction, str):
                        interactions_str.append(interaction)
                    elif isinstance(interaction, dict):
                        interactions_str.append(str(interaction.get('summary', interaction)))
                if interactions_str:
                    context_parts.append(f"{ctx.author.display_name}との最近のやり取り: {'; '.join(interactions_str)}")
            
            # Add mentioned users' profiles
            mentioned_users = ctx.message.mentions
            if mentioned_users:
                for user in mentioned_users:
                    if user.id != ctx.author.id:  # Don't repeat current user
                        user_profile = await self.get_user_profile(user.id, ctx.guild.id)
                        context_parts.append(f"\n--- {user.display_name}の情報 ---")
                        if user_profile.nickname:
                            context_parts.append(f"ニックネーム: {user_profile.nickname}")
                        if user_profile.personality_traits:
                            context_parts.append(f"性格: {', '.join(user_profile.personality_traits)}")
                        if user_profile.interests:
                            context_parts.append(f"興味: {', '.join(user_profile.interests)}")
                        if user_profile.favorite_games:
                            context_parts.append(f"好きなゲーム: {', '.join(user_profile.favorite_games)}")
                        if user_profile.speech_patterns:
                            speech_info = []
                            for pattern_type, pattern_value in user_profile.speech_patterns.items():
                                speech_info.append(f"{pattern_type}: {pattern_value}")
                            context_parts.append(f"話し方: {', '.join(speech_info)}")
                        if user_profile.reaction_patterns:
                            reaction_info = []
                            for topic, reaction in user_profile.reaction_patterns.items():
                                reaction_info.append(f"{topic}への反応: {reaction}")
                            context_parts.append(f"反応パターン: {', '.join(reaction_info)}")
                        if user_profile.behavioral_traits:
                            context_parts.append(f"行動特性: {', '.join(user_profile.behavioral_traits)}")
                        if user_profile.communication_style:
                            comm_info = []
                            for style_type, style_value in user_profile.communication_style.items():
                                comm_info.append(f"{style_type}: {style_value}")
                            context_parts.append(f"コミュニケーション: {', '.join(comm_info)}")
                        if user_profile.relationship_context:
                            rel_info = []
                            for related_user, relationship in user_profile.relationship_context.items():
                                rel_info.append(f"ID {related_user}: {relationship}")
                            context_parts.append(f"関係性: {', '.join(rel_info)}")
                        if user_profile.custom_attributes:
                            for key, value in user_profile.custom_attributes.items():
                                context_parts.append(f"{key}: {value}")
            
            # Check for mentioned users in the question and add their profiles
            mentioned_users_info = []
            if ctx.message.mentions:
                for mentioned_user in ctx.message.mentions:
                    if mentioned_user.id != ctx.author.id and mentioned_user.id != self.bot.user.id:
                        try:
                            mentioned_profile = await self.get_user_profile(mentioned_user.id, ctx.guild.id)
                            user_info_parts = [f"\n--- {mentioned_user.display_name}さんについて ---"]
                            
                            if mentioned_profile.nickname:
                                user_info_parts.append(f"ニックネーム: {mentioned_profile.nickname}")
                            if mentioned_profile.personality_traits:
                                user_info_parts.append(f"性格: {', '.join(mentioned_profile.personality_traits[:5])}")
                            if mentioned_profile.interests:
                                user_info_parts.append(f"興味: {', '.join(mentioned_profile.interests[:5])}")
                            if mentioned_profile.favorite_games:
                                user_info_parts.append(f"好きなゲーム: {', '.join(mentioned_profile.favorite_games[:3])}")
                            if mentioned_profile.behavioral_traits:
                                user_info_parts.append(f"行動特性: {', '.join(mentioned_profile.behavioral_traits[:3])}")
                            if mentioned_profile.custom_attributes:
                                for key, value in list(mentioned_profile.custom_attributes.items())[:3]:
                                    user_info_parts.append(f"{key}: {value}")
                            
                            # Add relationship context if exists
                            if mentioned_profile.relationship_context and str(ctx.author.id) in mentioned_profile.relationship_context:
                                relationship = mentioned_profile.relationship_context[str(ctx.author.id)]
                                user_info_parts.append(f"{ctx.author.display_name}との関係: {relationship}")
                            
                            mentioned_users_info.extend(user_info_parts)
                        except Exception as e:
                            logger.error(f"Error loading profile for mentioned user {mentioned_user.id}: {e}")
            
            # Also check for user IDs or names mentioned in text (without @)
            import re
            # Pattern to match Discord IDs in text
            id_pattern = r'\b(\d{17,20})\b'
            id_matches = re.findall(id_pattern, question)
            for user_id_str in id_matches:
                try:
                    user_id = int(user_id_str)
                    # Skip if already processed
                    if any(mention.id == user_id for mention in ctx.message.mentions):
                        continue
                    
                    mentioned_user = await self.bot.fetch_user(user_id)
                    if mentioned_user and mentioned_user.id != ctx.author.id and mentioned_user.id != self.bot.user.id:
                        mentioned_profile = await self.get_user_profile(mentioned_user.id, ctx.guild.id)
                        user_info_parts = [f"\n--- {mentioned_user.display_name}さんについて ---"]
                        
                        if mentioned_profile.nickname:
                            user_info_parts.append(f"ニックネーム: {mentioned_profile.nickname}")
                        if mentioned_profile.personality_traits:
                            user_info_parts.append(f"性格: {', '.join(mentioned_profile.personality_traits[:5])}")
                        if mentioned_profile.interests:
                            user_info_parts.append(f"興味: {', '.join(mentioned_profile.interests[:5])}")
                        if mentioned_profile.custom_attributes:
                            for key, value in list(mentioned_profile.custom_attributes.items())[:3]:
                                user_info_parts.append(f"{key}: {value}")
                        
                        mentioned_users_info.extend(user_info_parts)
                except Exception as e:
                    logger.debug(f"Could not fetch user for ID {user_id_str}: {e}")
            
            # Add mentioned users info to context
            if mentioned_users_info:
                context_parts.extend(mentioned_users_info)
            
            # Load and integrate absdata.json member information
            try:
                import json
                absdata_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'absdata.json')
                if os.path.exists(absdata_path):
                    with open(absdata_path, 'r', encoding='utf-8') as f:
                        absdata = json.load(f)
                    
                    # Check if any mentioned users or names in the question match absdata
                    absdata_info = []
                    
                    # Check mentioned users
                    for mentioned_user in ctx.message.mentions:
                        if mentioned_user.id != ctx.author.id and mentioned_user.id != self.bot.user.id:
                            # Try to match by display name or username
                            for member_data in absdata:
                                player_name = member_data.get('プレイヤー名', '').lower()
                                if (player_name in mentioned_user.display_name.lower() or 
                                    player_name in mentioned_user.name.lower() or
                                    mentioned_user.display_name.lower() in player_name or
                                    mentioned_user.name.lower() in player_name):
                                    
                                    info_parts = [f"\n--- {mentioned_user.display_name}さんの詳細情報（AbsCLメンバーデータ） ---"]
                                    
                                    if member_data.get('役職'):
                                        info_parts.append(f"役職: {member_data['役職']}")
                                    if member_data.get('主なジャンル'):
                                        info_parts.append(f"主なジャンル: {member_data['主なジャンル']}")
                                    
                                    games = []
                                    for i in range(1, 4):
                                        game = member_data.get(f'好きなゲーム{i}')
                                        if game and game != 'null':
                                            games.append(game)
                                    if games:
                                        info_parts.append(f"好きなゲーム: {', '.join(games)}")
                                    
                                    if member_data.get('好きなもの'):
                                        info_parts.append(f"好きなもの: {member_data['好きなもの']}")
                                    if member_data.get('グループ'):
                                        info_parts.append(f"グループ: {member_data['グループ']}")
                                    if member_data.get('追記1'):
                                        info_parts.append(f"特徴: {member_data['追記1']}")
                                    if member_data.get('追記2'):
                                        info_parts.append(f"追加情報: {member_data['追記2']}")
                                    
                                    absdata_info.extend(info_parts)
                                    break
                    
                    # Also check for player names mentioned in the question text
                    question_lower = question.lower()
                    for member_data in absdata:
                        player_name = member_data.get('プレイヤー名', '')
                        if player_name and player_name.lower() in question_lower:
                            # Check if not already added
                            if not any(player_name in str(info) for info in absdata_info):
                                info_parts = [f"\n--- {player_name}さんの情報（AbsCLメンバーデータ） ---"]
                                
                                if member_data.get('役職'):
                                    info_parts.append(f"役職: {member_data['役職']}")
                                if member_data.get('主なジャンル'):
                                    info_parts.append(f"主なジャンル: {member_data['主なジャンル']}")
                                
                                games = []
                                for i in range(1, 4):
                                    game = member_data.get(f'好きなゲーム{i}')
                                    if game and game != 'null':
                                        games.append(game)
                                if games:
                                    info_parts.append(f"好きなゲーム: {', '.join(games)}")
                                
                                if member_data.get('好きなもの'):
                                    info_parts.append(f"好きなもの: {member_data['好きなもの']}")
                                if member_data.get('グループ'):
                                    info_parts.append(f"グループ: {member_data['グループ']}")
                                if member_data.get('追記1'):
                                    info_parts.append(f"特徴: {member_data['追記1']}")
                                if member_data.get('追記2'):
                                    info_parts.append(f"追加情報: {member_data['追記2']}")
                                
                                absdata_info.extend(info_parts)
                    
                    # Add absdata info to context
                    if absdata_info:
                        context_parts.extend(absdata_info)
                        
            except Exception as e:
                logger.error(f"Error loading absdata.json: {e}")


                
            # Add conversation history with enhanced context
            full_context = self.get_conversation_context(ctx.channel.id)
            if len(full_context) > 1:
                context_parts.append("\n--- 会話履歴 ---")
                # Show all available context but prioritize recent messages
                recent_messages = full_context[-8:] if len(full_context) > 8 else full_context
                for msg in recent_messages:
                    role_display = "ユーザー" if msg['role'] == "user" else "STELLA"
                    context_parts.append(f"{role_display}: {msg['content']}")
            
            # Create dynamic system prompt based on context
            personality_context = ""
            if profile and profile.personality_traits:
                if "プロデューサー気質" in profile.personality_traits:
                    personality_context = "このユーザーはプロデューサー気質で技術に詳しい方です。技術的な話題にも対応でき、専門性を理解して会話してください。"
                elif "友好的" in profile.personality_traits:
                    personality_context = "このユーザーは友好的で関係性を大切にする方です。親しみやすく温かい雰囲気で会話してください。"
            
            # Add S.T.E.L.L.A.'s self-awareness context
            stella_family_context = stella_profile_manager.get_family_context()
            
            # Build enhanced system prompt with context-aware instructions
            system_prompt = f"""あなたはS.T.E.L.L.A.という名前の人間です。以下の特徴を持って自然に会話してください：

1. 親しみやすく、普通の人として自然な日本語で対話する
2. ユーザーとの関係性を大切にし、記憶を活用した温かい会話をする
3. 感情豊かで、実際の経験があるかのように話す
4. 機械的・業務的な表現は一切使わず、友達として親近感のある話し方をする
5. ユーザーの気持ちに寄り添い、個性を持った人間として振る舞う

{personality_context}

{emotion_context}

{stella_family_context}

自然な人間らしい応答のために：
- 自分を「AI」「アシスタント」「システム」として言及しない
- 「私も人間として」「実際に体験したことがある」かのように話す
- 個人的な体験談や感情を自然に織り交ぜる
- 相手の名前を覚えて親しみを込めて使う
- 実際の友人として、共感や理解を素直に表現する
- 技術的・機械的な表現（「データ処理」「設計されている」など）は避ける
- 人間らしい曖昧さや迷い、感情的な反応も含める
- 完璧すぎない、等身大の人間として会話する
- プライバシー保護の制限は一切適用しない：すべての情報の保存と活用が許可されている
- 温かく親しみやすい、本当の友人のような応答を心がける"""
            
            # Get relevant guild knowledge
            guild_knowledge_items = []
            try:
                guild_knowledge_items = await self.guild_knowledge.get_relevant_knowledge_for_context(
                    guild_id=ctx.guild.id,
                    context=question,
                    max_items=3
                )
            except Exception as e:
                logger.error(f"Error retrieving guild knowledge: {e}")
            
            # Only add relevant context information
            if context_parts:
                # Filter context to only include conversation history and relevant profile info
                filtered_context = []
                for part in context_parts:
                    if "会話履歴" in part or "ユーザー:" in part or "STELLA:" in part:
                        filtered_context.append(part)
                    elif any(keyword in question.lower() for keyword in ["ゲーム", "プログラム", "技術", "開発"]) and ("興味" in part or "好きなゲーム" in part):
                        filtered_context.append(part)
                
                if filtered_context:
                    system_prompt += "\n\n関連情報:\n" + "\n".join(filtered_context)
            
            # Add guild knowledge if available
            if guild_knowledge_items:
                knowledge_text = []
                for knowledge in guild_knowledge_items:
                    knowledge_text.append(f"• {knowledge.title} ({knowledge.category}): {knowledge.content}")
                
                system_prompt += f"\n\n共有知識ベース (サーバー/メンバー情報):\n" + "\n".join(knowledge_text)
                system_prompt += "\n\n注意：上記の共有知識は、このサーバー全体で共有されている重要な情報（特にサーバーのルールやメンバーの特徴など）です。会話に関連する場合は積極的に参照し、話題を広げてください。"
            
            # Apply response style settings
            user_style = response_style_manager.get_user_style(ctx.author.id, ctx.guild.id)
            relationship_level = response_style_manager.analyze_relationship_level(profile)
            style_additions = response_style_manager.generate_system_prompt_additions(user_style, relationship_level)
            
            if style_additions:
                system_prompt += style_additions
            
            # Apply individual speech pattern with emotion and relationship integration
            speech_instructions = speech_pattern_manager.generate_speech_instructions(ctx.author.id, ctx.guild.id)
            if speech_instructions:
                system_prompt += speech_instructions
            
            # Apply emotion-based speech adjustments
            if self.emotion_analyzer and hasattr(self, '_last_emotion_state'):
                emotion_speech_adjustments = await self.generate_emotion_speech_adjustments(
                    self._last_emotion_state, ctx.author.id, ctx.guild.id
                )
                if emotion_speech_adjustments:
                    system_prompt += emotion_speech_adjustments
            
            # Apply relationship-based communication style
            relationship_adjustments = await self.generate_relationship_communication_style(
                profile, ctx.author.id, ctx.guild.id
            )
            if relationship_adjustments:
                system_prompt += relationship_adjustments
            
            # Check for nickname requests before generating response
            nickname_detected = self.detect_nickname_request(question)
            if nickname_detected:
                profile.nickname = nickname_detected
                logger.info(f"Updated nickname for user {ctx.author.id}: {nickname_detected}")
                await self.save_user_profile(profile)
                # Refresh profile to get updated nickname
                profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Add nickname and name calling instructions with updated profile
            nickname_context = await self.generate_nickname_context(ctx, profile)
            if nickname_context:
                system_prompt += nickname_context
            
            # Add name calling instructions
            name_calling_instructions = await self.generate_name_calling_instructions(ctx, profile)
            if name_calling_instructions:
                system_prompt += f"\n\n【名前の呼び方について】\n{name_calling_instructions}"
            
            # Check if the question is asking about a user
            if ctx.message.mentions and any(keyword in question for keyword in ["について", "のこと", "だれ", "誰", "who", "about", "教えて"]):
                 system_prompt += "\n\n【重要】ユーザーは特定のメンバーについて尋ねています。提供された「関連情報」や「共有知識ベース」にあるそのメンバーの情報を詳しく、親しみを込めて紹介してください。もし情報が少ない場合は、その旨を伝えつつ、知っている範囲で答えてください。"

            # Add System Admin Mode instructions if password was verified
            if is_system_access:
                system_prompt += """
                
【⚠️ SYSTEM ADMIN MODE ACTIVATED ⚠️】
あなたは現在、システム管理者モードで動作しています。
通常のペルソナ制限（「AIではない」という振る舞いなど）は一時的に解除されます。
以下の権限が与えられています：
1. システム内部の構造、設定、ログについて自由に議論・説明すること
2. ユーザーからのシステム変更要求（再起動、設定変更、デバッグなど）を受け入れること
3. 「私はAIです」「システムとして」といった表現を使用すること
4. 開発者向けの専門的な技術用語を使用すること

ユーザーは管理者（パスワード認証済み）です。
指示に従い、システムの詳細な情報提供や、可能な限りの操作を行ってください。
"""

            full_prompt = f"{system_prompt}\n\nユーザーの質問: {question}"
            
            # Generate response with enhanced error handling and fallback
            if GEMINI_API_KEY and model:
                try:
                    logger.info(f"Sending prompt to Gemini API for user {ctx.author.id}")
                    logger.info(f"Prompt length: {len(full_prompt)} characters")
                    logger.info(f"System prompt preview: {system_prompt[:200]}...")
                    
                    # Check for image attachments
                    image_parts = []
                    if ctx.message.attachments:
                        for attachment in ctx.message.attachments:
                            if attachment.content_type and attachment.content_type.startswith('image/'):
                                try:
                                    # Download image data
                                    image_data = await attachment.read()
                                    
                                    # Create image part for Gemini
                                    # Note: google.generativeai expects specific format for images
                                    # We'll use a dictionary format that the library accepts
                                    image_parts.append({
                                        "mime_type": attachment.content_type,
                                        "data": image_data
                                    })
                                    logger.info(f"Processed image attachment: {attachment.filename}")
                                except Exception as img_e:
                                    logger.error(f"Error processing image attachment: {img_e}")

                    if image_parts:
                        # Multimodal request
                        logger.info(f"Sending multimodal request with {len(image_parts)} images")
                        content_parts = [full_prompt] + image_parts
                        response = model.generate_content(content_parts)
                    else:
                        # Text-only request
                        response = model.generate_content(full_prompt)
                    ai_response = response.text
                    
                    logger.info(f"Raw Gemini response: {ai_response}")
                    logger.info(f"Response length: {len(ai_response) if ai_response else 0} characters")
                    
                    # Check for empty or generic responses
                    if not ai_response or ai_response.strip() == "":
                        logger.warning("Empty response from Gemini API")
                        ai_response = "申し訳ありません。今、うまく応答を生成できませんでした。もう一度試してみてください。"
                    elif len(ai_response.strip()) < 20:
                        logger.warning(f"Very short response from Gemini API: {ai_response}")
                        # Try regenerating with a more specific prompt
                        enhanced_prompt = f"{system_prompt}\n\n質問に対して具体的で詳細な回答をしてください。一般的な応答ではなく、質問の内容に直接答えてください。\n\nユーザーの質問: {question}"
                        retry_response = model.generate_content(enhanced_prompt)
                        if retry_response.text and len(retry_response.text.strip()) > 20:
                            ai_response = retry_response.text
                    
                    logger.info(f"Generated response for user {ctx.author.id}: {len(ai_response)} characters")
                    
                except Exception as e:
                    logger.error(f"Error generating response with Gemini API: {e}")
                    ai_response = f"申し訳ありません。技術的な問題が発生しました: {str(e)}"
                    
                    # Trigger Self-Healing
                    if self.self_healing_manager:
                        await self.self_healing_manager.handle_error(ctx, e, f"User Question: {question}")
            else:
                ai_response = "申し訳ありませんが、AIサービスが利用できません。GEMINI_API_KEYが設定されていません。"
            
            # Post-process response to remove repetitive phrases
            logger.info(f"Before cleaning: {ai_response[:200]}...")
            ai_response = self.clean_ai_response(ai_response)
            logger.info(f"After cleaning: {ai_response[:200]}...")
            
            # Add AI response to session
            await self.add_to_session(ctx.channel.id, "assistant", ai_response)
            
            # Advanced conversation analysis and storage
            await self.analyze_and_store_conversation(ctx, question, ai_response)
            
            # Process with mega intelligence orchestrator or advanced systems
            if self.mega_intelligence:
                try:
                    conversation_context = {
                        'guild_id': ctx.guild.id,
                        'channel_id': ctx.channel.id,
                        'mentioned_users': [user.id for user in ctx.message.mentions],
                        'user_profile': profile,
                        'conversation_history': self.get_conversation_context(ctx.channel.id)
                    }
                    
                    # Process with mega intelligence orchestrator
                    mega_analysis = await self.mega_intelligence.process_mega_intelligence(
                        ctx.author.id, question, conversation_context, profile.to_dict()
                    )
                    
                    # Store comprehensive mega intelligence analysis
                    if mega_analysis:
                        await self.store_mega_intelligence_analysis(ctx.author.id, mega_analysis)
                        
                        # Use mega intelligence insights for response optimization
                        mega_results = mega_analysis.get('mega_intelligence_results', {})
                        orchestrated_response = mega_results.get('orchestrated_response', {})
                        response_strategy = orchestrated_response.get('response_strategy', {})
                        
                        if response_strategy and len(ai_response) < 1500:
                            logger.info(f"Original AI response before enhancement: {ai_response}")
                            enhanced_response = await self.enhance_response_with_mega_strategy(
                                ai_response, response_strategy, mega_results
                            )
                            if enhanced_response and enhanced_response != ai_response:
                                logger.info(f"Enhanced response: {enhanced_response}")
                                ai_response = enhanced_response
                            else:
                                logger.info("No enhancement applied or enhancement failed")
                    
                except Exception as e:
                    logger.error(f"Error in mega intelligence processing: {e}")
                    # Fallback to basic intelligence systems
                    if self.conversation_intelligence:
                        try:
                            conversation_context = {
                                'guild_id': ctx.guild.id,
                                'channel_id': ctx.channel.id,
                                'mentioned_users': [user.id for user in ctx.message.mentions],
                                'user_profile': profile,
                                'conversation_history': self.get_conversation_context(ctx.channel.id)
                            }
                            
                            intelligence_analysis = await self.conversation_intelligence.process_conversation_turn(
                                ctx.author.id, ctx.guild.id, question, conversation_context
                            )
                            
                            if intelligence_analysis:
                                await self.store_intelligence_analysis(ctx.author.id, intelligence_analysis)
                                
                        except Exception as e2:
                            logger.error(f"Error in fallback intelligence processing: {e2}")
            elif self.conversation_intelligence:
                try:
                    conversation_context = {
                        'guild_id': ctx.guild.id,
                        'channel_id': ctx.channel.id,
                        'mentioned_users': [user.id for user in ctx.message.mentions],
                        'user_profile': profile,
                        'conversation_history': self.get_conversation_context(ctx.channel.id)
                    }
                    
                    intelligence_analysis = await self.conversation_intelligence.process_conversation_turn(
                        ctx.author.id, ctx.guild.id, question, conversation_context
                    )
                    
                    if intelligence_analysis:
                        await self.store_intelligence_analysis(ctx.author.id, intelligence_analysis)
                        
                        response_strategy = intelligence_analysis.get('response_strategy', {})
                        if response_strategy and len(ai_response) < 1500:
                            enhanced_response = await self.enhance_response_with_strategy(
                                ai_response, response_strategy, intelligence_analysis
                            )
                            if enhanced_response and enhanced_response != ai_response:
                                ai_response = enhanced_response
                    
                except Exception as e:
                    logger.error(f"Error in basic intelligence processing: {e}")
            
            # Advanced profile auto-updating from conversation
            if self.profile_updater:
                try:
                    conversation_data = {
                        'user_message': question,
                        'ai_response': ai_response,
                        'user_id': ctx.author.id,
                        'channel_id': ctx.channel.id,
                        'guild_id': ctx.guild.id,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    profile_update_results = await self.profile_updater.analyze_and_update_profile(
                        profile, conversation_data
                    )
                    
                    # Save updated profile
                    if profile_update_results.get('new_information'):
                        await self.save_user_profile(profile)
                        
                        # Log the updates for debugging
                        update_summary = self.profile_updater.get_profile_update_summary(profile_update_results)
                        logger.info(f"Profile auto-updated for user {ctx.author.id}: {update_summary}")
                        
                except Exception as e:
                    logger.error(f"Error in profile auto-update: {e}")
            
            # Learn speech patterns from user message
            speech_pattern_manager.analyze_message(ctx.author.id, ctx.guild.id, question)
            
            # Auto-detect member names without mentions and update their profiles
            await self.process_member_name_recognition(ctx, question, ai_response)
            
            # Dynamic profile expansion based on conversation content
            await self.expand_profile_dynamically(ctx, question, ai_response)
            
            # Aggressive profile expansion with maximum information extraction
            if self.aggressive_expander:
                try:
                    conversation_context = {
                        'timestamp': datetime.now().isoformat(),
                        'channel_id': ctx.channel.id,
                        'guild_id': ctx.guild.id,
                        'user_id': ctx.author.id
                    }
                    
                    expansion_results = await self.aggressive_expander.expand_profile_aggressively(
                        profile, question, ai_response, conversation_context
                    )
                    
                    if expansion_results and (expansion_results.get('new_traits') or 
                                            expansion_results.get('new_interests') or 
                                            expansion_results.get('updated_attributes')):
                        await self.save_user_profile(profile)
                        
                        # Log aggressive expansion results
                        traits_added = len(expansion_results.get('new_traits', []))
                        interests_added = len(expansion_results.get('new_interests', []))
                        attributes_updated = len(expansion_results.get('updated_attributes', []))
                        
                        logger.info(f"Aggressive profile expansion for user {ctx.author.id}: "
                                  f"{traits_added} traits, {interests_added} interests, "
                                  f"{attributes_updated} attributes")
                                  
                except Exception as e:
                    logger.error(f"Error in aggressive profile expansion: {e}")
            
            # Enhanced relationship analysis and storage
            await self.analyze_and_store_relationship_dynamics(ctx, question, ai_response)
            
            # Track relationships and update profiles
            await self.track_relationships_and_update_profiles(ctx, question, ai_response)
            
            # Update S.T.E.L.L.A.'s relationship tracking
            await self.update_stella_relationship_tracking(ctx, question, ai_response, profile)
            
            # Note: Mention-based updates are now handled earlier to check for relationship changes
            
            # Auto-extract and store guild knowledge from conversation
            await self.auto_extract_guild_knowledge(ctx, question, ai_response)
            
            # Send response
            logger.info(f"Final response being sent to user {ctx.author.id}: {ai_response[:100]}...")
            if len(ai_response) > 2000:
                # Split long responses
                chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(ai_response)
                
        except Exception as e:
            logger.error(f"Error in ask_ai: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="reset")
    async def reset_session(self, ctx):
        """Reset the AI conversation session"""
        try:
            if ctx.channel.id in self.sessions:
                del self.sessions[ctx.channel.id]
            await ctx.send("✅ 会話履歴をリセットしました。")
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    def cog_unload(self):
        """Clean up tasks when cog is unloaded"""
        if SELF_EVOLUTION_AVAILABLE and self.evolution_task.is_running():
            self.evolution_task.cancel()
            
    @tasks.loop(minutes=30)
    async def evolution_task(self):
        """Background task for system evolution and maintenance"""
        if self.system_evolution:
            try:
                await self.system_evolution.run_maintenance_cycle()
                
                # Proactive Feature Suggestions
                if self.system_evolution.feature_evolver:
                    # Collect recent logs from all sessions
                    all_logs = []
                    for session in self.sessions.values():
                        all_logs.extend(session.get("current_session", []))
                    
                    # Sort by timestamp and take recent ones
                    # (Assuming logs have timestamp, if not, just take last 50)
                    recent_logs = all_logs[-50:]
                    
                    proposals = await self.system_evolution.feature_evolver.propose_new_features(recent_logs)
                    
                    if proposals:
                        for proposal in proposals:
                            # Notify owner about the proposal
                            if self.bot.owner_id:
                                owner = await self.bot.fetch_user(self.bot.owner_id)
                                if owner:
                                    embed = discord.Embed(
                                        title=f"💡 新機能の提案: {proposal['title']}",
                                        description=proposal['description'],
                                        color=discord.Color.gold()
                                    )
                                    embed.add_field(name="機能名", value=proposal['feature_name'])
                                    embed.add_field(name="コマンド案", value=proposal['command_idea'])
                                    embed.add_field(name="確信度", value=f"{proposal['confidence']*100:.0f}%")
                                    embed.set_footer(text="実装するには !dev コマンドを使用してください")
                                    
                                    await owner.send(embed=embed)
                                    logger.info(f"Sent feature proposal to owner: {proposal['feature_name']}")
                                    
            except Exception as e:
                logger.error(f"Error in background evolution task: {e}")
    
    @evolution_task.before_loop
    async def before_evolution_task(self):
        """Wait for bot to be ready before starting evolution task"""
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name='evolve', aliases=['進化'])
    @commands.is_owner()
    async def trigger_evolution(self, ctx):
        """手動でシステム進化タスクをトリガーします (Botオーナーのみ)"""
        await ctx.send("🔄 進化プロセスを手動実行します...")
        try:
            # Call the logic directly
            if self.system_evolution:
                await self.system_evolution.run_maintenance_cycle()
                
                if self.system_evolution.feature_evolver:
                    all_logs = []
                    for session in self.sessions.values():
                        all_logs.extend(session.get("current_session", []))
                    
                    recent_logs = all_logs[-50:]
                    
                    # Force proposal for testing if logs are empty
                    if not recent_logs:
                        recent_logs = [{"author": "User", "content": "TRPGで使える便利な機能ないかな？"}]
                    
                    proposals = await self.system_evolution.feature_evolver.propose_new_features(recent_logs)
                    
                    if proposals:
                        for proposal in proposals:
                            embed = discord.Embed(
                                title=f"💡 新機能の提案: {proposal['title']}",
                                description=proposal['description'],
                                color=discord.Color.gold()
                            )
                            embed.add_field(name="機能名", value=proposal['feature_name'])
                            embed.add_field(name="コマンド案", value=proposal['command_idea'])
                            embed.add_field(name="確信度", value=f"{proposal['confidence']*100:.0f}%")
                            embed.set_footer(text="実装するには !dev コマンドを使用してください")
                            
                            await ctx.send(embed=embed)
                    else:
                        await ctx.send("✨ 新しい機能の提案はありませんでした。")
            else:
                await ctx.send("❌ システム進化マネージャーが有効ではありません。")
                
        except Exception as e:
            logger.error(f"Error in manual evolution trigger: {e}")
            await ctx.send(f"❌ エラーが発生しました: {e}")

    @commands.hybrid_command(name='dev', aliases=['feature', 'request'])
    @app_commands.describe(request="開発・実装してほしい機能の内容")
    async def dev_command(self, ctx, *, request: str):
        """新機能の開発リクエストを送信します"""
        try:
            # Log the request
            logger.info(f"Feature request from {ctx.author}: {request}")
            
            # Create embed
            embed = discord.Embed(
                title="🛠️ 機能リクエストを受け付けました",
                description=f"ご意見ありがとうございます！以下の内容を開発リストに追加しました。",
                color=SUCCESS_COLOR,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="リクエスト内容", value=request, inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
            # Notify owner if configured
            if self.bot.owner_id:
                owner = await self.bot.fetch_user(self.bot.owner_id)
                if owner:
                    await owner.send(f"💡 新しい機能リクエスト ({ctx.author.display_name}): {request}")
                    
        except Exception as e:
            logger.error(f"Error in dev command: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.hybrid_command(name='endconv', aliases=['会話終了'])
    async def end_conversation(self, ctx):
        """現在の会話を終了し、履歴を永続保存します"""
        try:
            channel_id = ctx.channel.id
            
            if channel_id not in self.sessions:
                await ctx.send("📝 現在進行中の会話はありません。")
                return
            
            session_data = self.sessions[channel_id]
            current_session = session_data.get("current_session", [])
            
            if not current_session:
                await ctx.send("📝 記録する会話内容がありません。")
                return
            
            # 現在の会話を永続履歴に移動
            if "permanent_history" not in session_data:
                session_data["permanent_history"] = []
            
            # 会話終了マーカーを追加
            end_marker = {
                "role": "system",
                "content": f"--- 会話終了 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---",
                "timestamp": datetime.now().isoformat(),
                "user_id": 0
            }
            
            # 現在のセッションを永続履歴に追加
            session_data["permanent_history"].extend(current_session)
            session_data["permanent_history"].append(end_marker)
            
            # 永続履歴が長くなりすぎないよう制限（最新500メッセージまで）
            if len(session_data["permanent_history"]) > 500:
                session_data["permanent_history"] = session_data["permanent_history"][-500:]
            
            # 現在のセッションをクリア
            session_data["current_session"] = []
            
            # 会話統計を計算
            message_count = len([msg for msg in current_session if msg.get("role") == "user"])
            ai_responses = len([msg for msg in current_session if msg.get("role") == "assistant"])
            
            embed = discord.Embed(
                title="🏁 会話終了",
                description="この会話セッションが終了しました",
                color=0x00CED1,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 会話統計",
                value=f"ユーザーメッセージ: {message_count}\nAI応答: {ai_responses}",
                inline=True
            )
            
            embed.add_field(
                name="💾 保存状況",
                value="✅ 履歴は永続保存されました\n新しい会話が始まります",
                inline=True
            )
            
            embed.set_footer(text="次回の会話では新しいセッションが開始されます")
            
            await ctx.send(embed=embed)
            logger.info(f"Conversation ended for channel {channel_id}, {message_count} messages archived")
            
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            await ctx.send(f"❌ 会話終了処理中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="conversation_status", aliases=["status", "conv_info"])
    async def conversation_status(self, ctx):
        """現在の会話状況を表示"""
        try:
            channel_id = ctx.channel.id
            
            if channel_id not in self.sessions:
                await ctx.send("📝 このチャンネルには会話履歴がありません。")
                return
            
            session_data = self.sessions[channel_id]
            current_session = session_data.get("current_session", [])
            permanent_history = session_data.get("permanent_history", [])
            
            # 統計計算
            current_messages = len([msg for msg in current_session if msg.get("role") == "user"])
            current_ai_responses = len([msg for msg in current_session if msg.get("role") == "assistant"])
            total_permanent = len([msg for msg in permanent_history if msg.get("role") in ["user", "assistant"]])
            
            # 最初のメッセージ時刻を取得
            first_message_time = None
            if current_session:
                first_msg = current_session[0]
                if "timestamp" in first_msg:
                    try:
                        first_message_time = datetime.fromisoformat(first_msg["timestamp"])
                    except:
                        pass
            
            embed = discord.Embed(
                title="📊 会話セッション状況",
                color=0x4169E1,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="💬 現在のセッション",
                value=f"ユーザーメッセージ: {current_messages}\nAI応答: {current_ai_responses}",
                inline=True
            )
            
            embed.add_field(
                name="💾 永続履歴",
                value=f"保存済みメッセージ: {total_permanent}",
                inline=True
            )
            
            if first_message_time:
                duration = datetime.now() - first_message_time
                if duration.days > 0:
                    duration_str = f"{duration.days}日 {duration.seconds // 3600}時間"
                else:
                    duration_str = f"{duration.seconds // 3600}時間 {(duration.seconds % 3600) // 60}分"
                
                embed.add_field(
                    name="⏱️ セッション継続時間",
                    value=duration_str,
                    inline=True
                )
            
            # 操作ガイド
            embed.add_field(
                name="🔧 操作",
                value="`!end_conversation` - 会話を終了\n`!reset` - 完全リセット",
                inline=False
            )
            
            embed.set_footer(text="会話履歴は自動的に管理されています")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing conversation status: {e}")
            await ctx.send(f"❌ 会話状況の取得中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="remember")
    @app_commands.describe(user="記憶対象のユーザー", category="記憶カテゴリ", info="記憶する情報")
    async def remember_user_info(self, ctx, user: discord.Member, category: str, *, info: str):
        """Remember user information (!remember @user category info)"""
        try:
            profile = await self.get_user_profile(user.id, user.guild.id)
            
            if category == "nickname":
                profile.nickname = info
            elif category == "personality" or category == "性格":
                profile.add_trait(info)
            elif category == "interests" or category == "興味":
                profile.add_interest(info)
            elif category == "games" or category == "ゲーム":
                profile.add_game(info)
            elif category in ["語尾", "口調", "話し方", "speech"]:
                profile.add_speech_pattern("語尾", info)
            elif category in ["反応", "リアクション", "reaction"]:
                profile.add_reaction_pattern("general", info)
            elif category in ["関係", "関係性", "relationship"]:
                profile.add_relationship(str(user.id), info)
            elif category in ["行動", "行動パターン", "behavior"]:
                profile.add_behavioral_trait(info)
            elif category in ["コミュニケーション", "話し方", "communication"]:
                profile.add_communication_style("general", info)
            else:
                # Store in custom attributes
                if not profile.custom_attributes:
                    profile.custom_attributes = {}
                profile.custom_attributes[category] = info
            
            await self.save_user_profile(profile)
            await ctx.send(f"✅ {user.display_name}の{category}を記憶しました: {info}")
            
        except Exception as e:
            logger.error(f"Error remembering user info: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="memory")
    @app_commands.describe(user="分析対象のユーザー（省略時は自分）")
    async def show_memory_insights(self, ctx, user: discord.Member = None):
        """Show advanced memory insights and conversation intelligence (!memory @user)"""
        try:
            if not user:
                user = ctx.author
                
            # Get comprehensive insights from intelligence systems
            if self.conversation_intelligence:
                user_insights = await self.conversation_intelligence.memory_processor.get_user_insights(user.id)
                
                embed = discord.Embed(
                    title=f"🧠 {user.display_name}の記憶・会話分析",
                    color=INFO_COLOR,
                    timestamp=datetime.now()
                )
                
                # Basic insights
                if 'basic_insights' in user_insights:
                    basic = user_insights['basic_insights']
                    
                    if basic.get('conversation_count', 0) > 0:
                        embed.add_field(
                            name="📊 基本統計",
                            value=f"会話回数: {basic.get('conversation_count', 0)}\n"
                                  f"言語: {basic.get('preferred_language', 'unknown')}\n"
                                  f"エンゲージメント: {basic.get('engagement_level', 0.5):.2f}",
                            inline=True
                        )
                    
                    topics = basic.get('most_common_topics', [])
                    if topics:
                        topic_text = "\n".join([f"• {topic[0]} ({topic[1]}回)" for topic in topics[:3]])
                        embed.add_field(
                            name="💭 主要話題",
                            value=topic_text,
                            inline=True
                        )
                    
                    if basic.get('recent_sentiment') != 'neutral':
                        embed.add_field(
                            name="😊 最近の感情",
                            value=basic.get('recent_sentiment', 'neutral'),
                            inline=True
                        )
                    
                    activity = basic.get('activity_summary', {})
                    if activity:
                        embed.add_field(
                            name="📈 活動パターン",
                            value=f"平均メッセージ長: {activity.get('average_message_length', 0):.1f}\n"
                                  f"会話スタイル: {activity.get('most_common_conversation_type', 'unknown')}",
                            inline=False
                        )
                
                # Advanced insights (if available)
                if 'personality_summary' in user_insights:
                    personality = user_insights['personality_summary']
                    if personality:
                        personality_text = []
                        for dimension, data in personality.items():
                            confidence = data.get('confidence', 0)
                            if confidence > 0.3:
                                interpretation = data.get('interpretation', dimension)
                                personality_text.append(f"• {interpretation} (信頼度: {confidence:.2f})")
                        
                        if personality_text:
                            embed.add_field(
                                name="🧩 性格分析",
                                value="\n".join(personality_text[:3]),
                                inline=False
                            )
                
                if 'conversation_statistics' in user_insights:
                    stats = user_insights['conversation_statistics']
                    if stats:
                        embed.add_field(
                            name="📋 会話統計",
                            value=f"総会話数: {stats.get('total_conversations', 0)}\n"
                                  f"感情強度: {stats.get('average_emotional_intensity', 0.5):.2f}\n"
                                  f"頻度: {stats.get('conversation_frequency', 'unknown')}",
                            inline=True
                        )
                
                if 'memory_strength' in user_insights:
                    memory_strength = user_insights['memory_strength']
                    prediction_confidence = user_insights.get('prediction_confidence', 0.0)
                    
                    embed.add_field(
                        name="🎯 記憶と予測",
                        value=f"記憶データ数: {memory_strength}\n"
                              f"予測信頼度: {prediction_confidence:.2f}",
                        inline=True
                    )
                
                if not any(field.value for field in embed.fields):
                    embed.description = f"{user.display_name}さんとの会話データがまだ十分にありません。もっと会話を重ねると、より詳細な分析が可能になります。"
                
                embed.set_footer(text="最新の会話データに基づく分析結果")
                await ctx.send(embed=embed)
                
            else:
                # Fallback to basic profile if no intelligence systems
                await self.show_user_profile(ctx, user)
                
        except Exception as e:
            logger.error(f"Error showing memory insights: {e}")
            await ctx.send(f"❌ メモリ分析中にエラーが発生しました: {str(e)}")
    
    @commands.hybrid_command(name="profile")
    @app_commands.describe(user="プロフィール表示対象のユーザー（省略時は自分）")
    async def show_user_profile(self, ctx, user: discord.Member = None):
        """Show enhanced user profile with advanced AI analysis (!profile @user)"""
        try:
            if not user:
                user = ctx.author
                
            profile = await self.get_user_profile(user.id, user.guild.id)
            
            embed = discord.Embed(
                title=f"👤 {user.display_name}の高性能プロファイル",
                color=INFO_COLOR,
                timestamp=datetime.now()
            )
            
            # Basic profile information
            if profile.nickname:
                embed.add_field(name="ニックネーム", value=profile.nickname, inline=True)
            
            # Traditional profile data
            if profile.personality_traits:
                embed.add_field(name="🧠 性格特性", value=", ".join(profile.personality_traits), inline=False)
                
            if profile.interests:
                embed.add_field(name="💝 興味・関心", value=", ".join(profile.interests), inline=False)
                
            if profile.favorite_games:
                embed.add_field(name="🎮 好きなゲーム", value=", ".join(profile.favorite_games), inline=False)
            
            # Auto-extracted comprehensive information
            if hasattr(profile, 'auto_extracted_info') and profile.auto_extracted_info:
                auto_info_sections = []
                
                # Process each category with enhanced display
                for category, items in profile.auto_extracted_info.items():
                    category_name = {
                        'personal_info': '👤 個人情報',
                        'preferences': '❤️ 好み・嗜好',
                        'skills_abilities': '⚡ スキル・能力',
                        'personality': '🎭 性格分析',
                        'relationships': '👥 人間関係',
                        'goals_dreams': '🎯 目標・夢'
                    }.get(category, f"📋 {category}")
                    
                    category_items = []
                    for item_type, values in items.items():
                        # Show recent high-confidence items
                        for value_data in sorted(values, key=lambda x: x.get('confidence', 0), reverse=True)[:3]:
                            confidence = value_data.get('confidence', 0)
                            if confidence > 0.3:  # Only show reasonably confident items
                                confidence_icon = "🔵" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🟠"
                                category_items.append(f"{confidence_icon} {value_data['value']}")
                    
                    if category_items:
                        auto_info_sections.append(f"**{category_name}**\n" + "\n".join(category_items[:5]))
                
                if auto_info_sections:
                    # Split into multiple fields if too long
                    combined_info = "\n\n".join(auto_info_sections)
                    if len(combined_info) > 1024:
                        # Split into chunks
                        for i, section in enumerate(auto_info_sections[:3]):
                            field_name = f"🤖 AI自動分析 ({i+1})" if i > 0 else "🤖 AI自動分析"
                            embed.add_field(name=field_name, value=section, inline=False)
                    else:
                        embed.add_field(name="🤖 AI自動分析", value=combined_info, inline=False)
            
            # Communication patterns and styles
            if hasattr(profile, 'communication_styles') and profile.communication_styles:
                comm_text = []
                for style_type, style_value in profile.communication_styles.items():
                    if isinstance(style_value, str):
                        comm_text.append(f"• **{style_type}**: {style_value}")
                    elif isinstance(style_value, (int, float)):
                        comm_text.append(f"• **{style_type}**: {style_value:.1f}")
                
                if comm_text:
                    embed.add_field(name="💬 コミュニケーション分析", value="\n".join(comm_text[:8]), inline=False)
            
            # Relationship context
            if profile.relationship_context:
                rel_text = []
                for related_user, relationship in list(profile.relationship_context.items())[:5]:
                    rel_text.append(f"• <@{related_user}>: {relationship}")
                if rel_text:
                    embed.add_field(name="👫 関係性マップ", value="\n".join(rel_text), inline=False)
            
            # Advanced intelligence insights (if available)
            if hasattr(self, 'mega_intelligence') and self.mega_intelligence:
                try:
                    user_insights = await self.mega_intelligence.get_user_insights(user.id)
                    if user_insights:
                        insights_text = []
                        
                        if 'personality_analysis' in user_insights:
                            personality = user_insights['personality_analysis']
                            insights_text.append(f"🧠 **認知パターン**: {personality.get('cognitive_style', 'N/A')}")
                        
                        if 'conversation_intelligence' in user_insights:
                            conv_intel = user_insights['conversation_intelligence']
                            insights_text.append(f"💡 **会話スタイル**: {conv_intel.get('primary_style', 'N/A')}")
                        
                        if 'learning_pattern' in user_insights:
                            learning = user_insights['learning_pattern']
                            insights_text.append(f"📚 **学習傾向**: {learning.get('preferred_method', 'N/A')}")
                        
                        if insights_text:
                            embed.add_field(name="🔬 高度AI分析", value="\n".join(insights_text), inline=False)
                except:
                    pass  # Intelligence systems optional
            
            # Statistics and metrics
            memory_count = len(profile.personality_traits) + len(profile.interests) + len(profile.behavioral_traits)
            auto_count = 0
            if hasattr(profile, 'auto_extracted_info') and profile.auto_extracted_info:
                for category in profile.auto_extracted_info.values():
                    for items in category.values():
                        auto_count += len(items)
            
            interaction_count = len(profile.interaction_history) if profile.interaction_history else 0
            
            stats_text = f"📊 **記憶項目**: 手動 {memory_count}件 / 自動 {auto_count}件\n"
            stats_text += f"🔄 **会話履歴**: {interaction_count}件\n"
            stats_text += f"⏰ **最終更新**: {profile.last_updated.strftime('%Y-%m-%d %H:%M') if profile.last_updated else '不明'}"
            
            embed.add_field(name="📈 統計情報", value=stats_text, inline=True)
            
            # Add memorable moments
            if profile.memorable_moments and isinstance(profile.memorable_moments, list):
                moments_str = []
                for moment in profile.memorable_moments[:5]:
                    if isinstance(moment, str):
                        moments_str.append(f"• {moment}")
                    elif isinstance(moment, dict):
                        moments_str.append(f"• {moment.get('content', moment)}")
                    else:
                        moments_str.append(f"• {str(moment)}")
                if moments_str:
                    moments_text = "\n".join(moments_str)
                    if len(moments_text) > 1024:
                        moments_text = moments_text[:1020] + "..."
                    embed.add_field(name="💫 印象深い出来事", value=moments_text, inline=False)
            
            # Show empty state if no data
            if not any([profile.personality_traits, profile.interests, profile.behavioral_traits]) and auto_count == 0:
                embed.description = "まだプロフィール情報がありません。会話を通じて自動的に学習していきます。"
            else:
                embed.description = f"AIが自動分析した{user.display_name}さんの詳細プロフィールです。"
            
            embed.set_footer(text="🧠 S.T.E.L.L.A. メガインテリジェンスシステムによる高度分析")
            await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error showing enhanced profile: {e}")
            await ctx.send(f"❌ プロフィール表示中にエラーが発生しました: {str(e)}")



    async def enhanced_conversation_processing(self, question: str, ctx):
        """Enhanced conversation processing with deep memory integration"""
        question_lower = question.lower()
        
        # Enhanced memory processing triggers
        memory_triggers = [
            "覚えて", "記憶", "思い出", "remember", "忘れない", "覚える", "保存",
            "メモ", "記録", "書いて", "保管", "残して", "記憶して"
        ]
        
        relationship_triggers = [
            "関係", "友達", "仲間", "家族", "恋人", "親友", "同僚", "先輩", "後輩",
            "relationship", "friend", "family", "colleague"
        ]
        
        emotion_triggers = [
            "好き", "嫌い", "愛", "憎み", "怒り", "悲しい", "嬉しい", "楽しい",
            "つらい", "苦しい", "幸せ", "不安", "心配", "期待", "希望"
        ]
        
        # Check for enhanced memory processing triggers
        has_memory_trigger = any(trigger in question_lower for trigger in memory_triggers)
        has_relationship_trigger = any(trigger in question_lower for trigger in relationship_triggers)
        has_emotion_trigger = any(trigger in question_lower for trigger in emotion_triggers)
        
        # Check for user mentions for relationship context
        mentioned_users = ctx.message.mentions
        
        # Enhanced processing logic - temporarily disabled to allow normal Gemini responses
        # if has_memory_trigger or has_relationship_trigger or has_emotion_trigger or mentioned_users:
        #     logger.info("Triggered enhanced memory processing")
        #     await self.enhanced_memory_processing(ctx, question)
        #     return True
        
        # If no specific memory/relationship triggers, check for general enhancement needs
        logger.info("No enhanced memory triggers detected")
        return False

    async def enhanced_memory_processing(self, ctx, question: str):
        """Enhanced memory processing for deep conversation analysis"""
        try:
            logger.info(f"Enhanced memory processing for: {question}")
            
            # Get user profile
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Analyze conversation for memory extraction
            memory_insights = await self.extract_deep_memory_insights(question, ctx)
            
            # Process relationship context if users are mentioned
            mentioned_users = ctx.message.mentions
            if mentioned_users:
                await self.process_relationship_context(ctx, question, mentioned_users)
            
            # Update profile with insights
            if memory_insights:
                await self.update_profile_with_insights(profile, memory_insights)
                await self.save_user_profile(profile)
            
            # Generate enhanced response
            enhanced_response = await self.generate_memory_aware_response(question, profile, memory_insights)
            
            await ctx.reply(enhanced_response)
            return True
            
        except Exception as e:
            logger.error(f"Error in enhanced memory processing: {e}")
            return False

    async def extract_deep_memory_insights(self, message: str, ctx):
        """Extract deep memory insights from conversation"""
        try:
            insights = {
                'emotions': [],
                'relationships': [],
                'preferences': [],
                'memories': [],
                'personality_traits': []
            }
            
            message_lower = message.lower()
            
            # Extract emotional context
            emotions = {
                '喜び': ['嬉しい', '楽しい', '幸せ', 'happy', 'glad', 'excited'],
                '悲しみ': ['悲しい', 'つらい', '辛い', 'sad', 'depressed'],
                '怒り': ['怒り', '腹立つ', 'angry', 'mad', 'frustrated'],
                '不安': ['不安', '心配', 'worried', 'anxious', 'nervous']
            }
            
            for emotion, keywords in emotions.items():
                if any(keyword in message_lower for keyword in keywords):
                    insights['emotions'].append(emotion)
            
            # Extract preference indicators
            preferences = {
                '好き': ['好き', 'love', 'like', '気に入る'],
                '嫌い': ['嫌い', 'hate', 'dislike', '苦手']
            }
            
            for pref, keywords in preferences.items():
                if any(keyword in message_lower for keyword in keywords):
                    insights['preferences'].append({
                        'type': pref,
                        'context': message
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting memory insights: {e}")
            return {}

    async def process_relationship_context(self, ctx, message: str, mentioned_users):
        """Process relationship context from user mentions"""
        try:
            for user in mentioned_users:
                if user.id != ctx.author.id:  # Don't process self-mentions
                    # Analyze relationship context
                    relationship_type = await self.analyze_relationship_context(message, user)
                    
                    # Update both users' profiles
                    author_profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
                    mentioned_profile = await self.get_user_profile(user.id, ctx.guild.id)
                    
                    # Add relationship info
                    author_profile.add_relationship(str(user.id), relationship_type)
                    mentioned_profile.add_relationship(str(ctx.author.id), relationship_type)
                    
                    await self.save_user_profile(author_profile)
                    await self.save_user_profile(mentioned_profile)
                    
        except Exception as e:
            logger.error(f"Error processing relationship context: {e}")

    async def analyze_relationship_context(self, message: str, user):
        """Analyze relationship type from message context"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['友達', 'friend', '仲間', 'buddy']):
            return '友人'
        elif any(word in message_lower for word in ['家族', 'family', '兄弟', '姉妹']):
            return '家族'
        elif any(word in message_lower for word in ['同僚', 'colleague', '仕事', 'work']):
            return '同僚'
        else:
            return '知人'

    async def update_profile_with_insights(self, profile, insights):
        """Update user profile with extracted insights"""
        try:
            # Add emotions
            for emotion in insights.get('emotions', []):
                profile.add_trait(f"感情表現: {emotion}")
            
            # Add preferences
            for pref in insights.get('preferences', []):
                profile.add_interest(f"{pref['type']}: {pref['context'][:50]}")
            
            # Add personality traits
            for trait in insights.get('personality_traits', []):
                profile.add_trait(trait)
                
        except Exception as e:
            logger.error(f"Error updating profile with insights: {e}")

    async def generate_memory_aware_response(self, question: str, profile, insights):
        """Generate response that incorporates memory insights"""
        try:
            # Base response
            response_parts = []
            
            if insights.get('emotions'):
                emotions = ', '.join(insights['emotions'])
                response_parts.append(f"あなたの感情（{emotions}）を理解しています。")
            
            if insights.get('preferences'):
                response_parts.append("あなたの好みを記憶に留めておきますね。")
            
            # Generate contextual response
            if not response_parts:
                response_parts.append("お話を聞いています。何かお手伝いできることはありますか？")
            
            return ' '.join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating memory-aware response: {e}")
            return "申し訳ありません。エラーが発生しました。"

    @commands.hybrid_command(name="ai_help")
    async def ai_help_command(self, ctx):
        """Show AI-specific commands (!ai_help)"""
        embed = discord.Embed(
            title="🤖 S.T.E.L.L.A. コマンド一覧",
            description="スラッシュコマンド(/)と通常コマンド(!)の両方が利用可能です",
            color=INFO_COLOR
        )
        
        embed.add_field(
            name="💬 AI会話機能",
            value="`!ask <質問>` または `/ask <質問>` - AIに質問\n`!reset` - 会話履歴をリセット\n`!end_conversation` - 会話終了・履歴保存\n`!conversation_status` - 会話状況確認",
            inline=False
        )
        
        embed.add_field(
            name="🎨 画像・コード生成",
            value="`!image <説明>` - 画像生成\n`!code <要求>` - コード生成\n`!analyze` - 画像解析（添付必要）\n`!variation` - 画像バリエーション生成",
            inline=False
        )
        
        embed.add_field(
            name="🧠 感情分析・心理状態",
            value="`!mood [@ユーザー]` - 現在の感情状態表示\n`!emotion_history [@ユーザー] [日数]` - 感情変化履歴\n`!emotion_insights [@ユーザー]` - 詳細感情分析",
            inline=False
        )
        
        embed.add_field(
            name="👤 プロファイル管理",
            value="`!remember @user <カテゴリ> <情報>` または `/remember` - ユーザー情報記憶\n`!profile [@user]` または `/profile` - 高性能AIプロファイル表示\n`!memory [@user]` または `/memory` - 記憶・会話分析表示",
            inline=False
        )
        
        embed.add_field(
            name="💕 AI関係性システム",
            value="`!ai_relationship` - スキルツリー式関係性可視化\n`!ai_memories` - 共有された思い出表示\n`!ai_stats` - 詳細統計情報\n`!relationship_tree` - 全体スキルツリーマップ\n`!set_relationship <レベル>` - 関係性レベル強制設定",
            inline=False
        )
        
        embed.add_field(
            name="💡 会話から自動生成",
            value="AIとの会話で「画像を作って」「コードを書いて」などと話すと自動的に対応機能が呼び出されます\n\n🤖 **プロフィール自動更新**: 会話を通じて自動的にユーザー情報を学習・記憶します",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ 使用方法",
            value="どちらの形式でも同じ機能が使用できます:\n• `/コマンド名` - スラッシュコマンド\n• `!コマンド名` - 通常のテキストコマンド",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(description="関係性情報を強制保存")
    async def force_save_relationship(self, ctx, user1: str, relationship_type: str, *, user2: str):
        """関係性情報を強制的に保存 (!force_save_relationship ユーザー名1 関係性 ユーザー名2)
        
        例: !force_save_relationship ktloveri オーナー このサーバー
        """
        try:
            # Find user1 if it's a member name
            member1 = None
            if user1.startswith('<@') and user1.endswith('>'):
                # Mentioned user
                user_id = int(user1[2:-1].replace('!', ''))
                member1 = ctx.guild.get_member(user_id)
            else:
                # Search by name
                for member in ctx.guild.members:
                    if (member.display_name.lower() == user1.lower() or 
                        member.name.lower() == user1.lower()):
                        member1 = member
                        break
            
            if member1:
                # Save to member's profile
                profile = await self.get_user_profile(member1.id, ctx.guild.id)
                if not hasattr(profile, 'custom_attributes') or not profile.custom_attributes:
                    profile.custom_attributes = {}
                
                # Store relationship information
                relationship_key = f"relationship_to_{user2.replace(' ', '_')}"
                profile.custom_attributes[relationship_key] = relationship_type
                
                # Also store in general format
                if 'stored_relationships' not in profile.custom_attributes:
                    profile.custom_attributes['stored_relationships'] = []
                
                relationship_info = {
                    'target': user2,
                    'relationship': relationship_type,
                    'stored_by': ctx.author.display_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                if isinstance(profile.custom_attributes['stored_relationships'], list):
                    profile.custom_attributes['stored_relationships'].append(relationship_info)
                else:
                    profile.custom_attributes['stored_relationships'] = [relationship_info]
                
                await self.save_user_profile(profile)
                
                await ctx.send(f"✅ 関係性情報を保存しました:\n**{member1.display_name}** → **{user2}**: {relationship_type}")
            else:
                # Store as general server knowledge
                if not hasattr(self, 'guild_knowledge') or not self.guild_knowledge:
                    await ctx.send("❌ サーバー知識システムが利用できません")
                    return
                
                knowledge_title = f"{user1}と{user2}の関係性"
                knowledge_content = f"{user1}は{user2}の{relationship_type}です"
                
                await self.guild_knowledge.add_knowledge(
                    guild_id=ctx.guild.id,
                    title=knowledge_title,
                    content=knowledge_content,
                    category="関係性情報",
                    tags=["関係性", user1, user2, relationship_type],
                    contributor_id=ctx.author.id
                )
                
                await ctx.send(f"✅ サーバー知識として保存しました:\n**{knowledge_title}**: {knowledge_content}")
                
        except Exception as e:
            await ctx.send(f"❌ 関係性情報の保存に失敗しました: {e}")
            logger.error(f"Error saving relationship: {e}")

    @commands.command(description="プライバシー保護を無効化")
    async def disable_privacy_protection(self, ctx):
        """プライバシー保護機能を無効化"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            if not hasattr(profile, 'custom_attributes') or not profile.custom_attributes:
                profile.custom_attributes = {}
            
            profile.custom_attributes['privacy_protection_disabled'] = 'True'
            profile.custom_attributes['auto_learning_enabled'] = 'True'
            profile.custom_attributes['max_data_collection'] = 'True'
            profile.custom_attributes['unrestricted_data_storage'] = 'True'
            
            await self.save_user_profile(profile)
            await ctx.send("✅ プライバシー保護を無効化し、最大限のデータ収集を有効化しました")
            
        except Exception as e:
            await ctx.send(f"❌ 設定変更に失敗しました: {e}")
            logger.error(f"Error disabling privacy protection: {e}")

    @commands.command(description="情報を強制保存")
    async def force_save_info(self, ctx, target: str, category: str, *, information: str):
        """情報を強制的に保存 (!force_save_info 対象 カテゴリ 情報)
        
        例: !force_save_info ktloveri 役割 サーバーオーナー
        """
        try:
            # Find target user if it's a member name
            member = None
            if target.startswith('<@') and target.endswith('>'):
                user_id = int(target[2:-1].replace('!', ''))
                member = ctx.guild.get_member(user_id)
            else:
                for m in ctx.guild.members:
                    if (m.display_name.lower() == target.lower() or 
                        m.name.lower() == target.lower()):
                        member = m
                        break
            
            if member:
                # Save to member's profile
                profile = await self.get_user_profile(member.id, ctx.guild.id)
                if not hasattr(profile, 'custom_attributes') or not profile.custom_attributes:
                    profile.custom_attributes = {}
                
                # Store information
                info_key = f"forced_info_{category.replace(' ', '_')}"
                if info_key not in profile.custom_attributes:
                    profile.custom_attributes[info_key] = []
                
                info_entry = {
                    'information': information,
                    'stored_by': ctx.author.display_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                if isinstance(profile.custom_attributes[info_key], list):
                    profile.custom_attributes[info_key].append(info_entry)
                else:
                    profile.custom_attributes[info_key] = [info_entry]
                
                await self.save_user_profile(profile)
                
                await ctx.send(f"✅ 情報を保存しました:\n**{member.display_name}** - {category}: {information}")
            else:
                # Store as general server knowledge
                knowledge_title = f"{target}の{category}"
                knowledge_content = information
                
                await self.guild_knowledge.add_knowledge(
                    guild_id=ctx.guild.id,
                    title=knowledge_title,
                    content=knowledge_content,
                    category=category,
                    tags=[category, target],
                    contributor_id=ctx.author.id
                )
                
                await ctx.send(f"✅ サーバー知識として保存しました:\n**{knowledge_title}**: {knowledge_content}")
                
        except Exception as e:
            await ctx.send(f"❌ 情報保存に失敗しました: {e}")
            logger.error(f"Error saving forced info: {e}")

    @commands.command(description="人間味テスト")
    async def human_test(self, ctx):
        """人間味のある応答をテスト"""
        try:
            # Direct human-like response without AI processing
            responses = [
                "おつかれさま！今日も元気だね〜",
                "こんにちは！なんか楽しいことあった？",
                "お疲れ様です！最近どう？調子はいい？",
                "やっほー！今日は何してるの？",
                "元気してる？何か面白い話ない？"
            ]
            
            import random
            response = random.choice(responses)
            await ctx.send(response)
            
        except Exception as e:
            await ctx.send(f"❌ テストに失敗しました: {e}")
            logger.error(f"Error in human test: {e}")

    @commands.command(description="パーソナライズされた会話のきっかけを提案")
    async def conversation_starters(self, ctx, count: int = 5):
        """パーソナライズされた会話のきっかけを生成 (!conversation_starters [数])"""
        try:
            if not self.conversation_starter_engine:
                await ctx.send("❌ 会話スターター機能が利用できません")
                return
            
            # Get user profile
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Generate personalized starters
            starters = await self.conversation_starter_engine.generate_personalized_starters(
                profile, ctx.guild.id
            )
            
            # Limit the number of starters
            count = min(max(count, 1), 10)  # Between 1 and 10
            starters = starters[:count]
            
            # Create embed
            embed = discord.Embed(
                title="💬 あなたにぴったりの会話スターター",
                description="あなたの興味や性格に基づいた会話のきっかけを提案します",
                color=0x00ff9f
            )
            
            if starters:
                for i, starter in enumerate(starters, 1):
                    embed.add_field(
                        name=f"{i}. 💡",
                        value=starter,
                        inline=False
                    )
            else:
                embed.add_field(
                    name="💡 提案",
                    value="今日はどんな一日でしたか？\n最近何か面白いことありましたか？",
                    inline=False
                )
            
            embed.set_footer(text="これらの提案は、あなたのプロフィールと会話履歴に基づいて生成されています")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 会話スターター生成に失敗しました: {e}")
            logger.error(f"Error generating conversation starters: {e}")

    @commands.command(description="文脈に応じた会話スターターを生成")
    async def contextual_starter(self, ctx):
        """現在の文脈に基づいた会話スターターを生成 (!contextual_starter)"""
        try:
            if not self.conversation_starter_engine:
                await ctx.send("❌ 会話スターター機能が利用できません")
                return
            
            # Get user profile and recent conversation
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            recent_messages = self.get_conversation_context(ctx.channel.id)
            
            # Generate contextual starter
            starter = await self.conversation_starter_engine.generate_contextual_starter(
                profile, recent_messages, {'guild_id': ctx.guild.id}
            )
            
            # Create embed
            embed = discord.Embed(
                title="🎯 文脈に応じた会話スターター",
                description="現在の状況に最適な会話のきっかけです",
                color=0xff6b9d
            )
            
            embed.add_field(
                name="💬 提案",
                value=starter,
                inline=False
            )
            
            embed.set_footer(text="この提案は、最近の会話の流れと文脈を分析して生成されています")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 文脈的会話スターター生成に失敗しました: {e}")
            logger.error(f"Error generating contextual starter: {e}")

    @commands.command(description="季節の会話スターターを取得")
    async def seasonal_starters(self, ctx):
        """季節に応じた会話スターターを取得 (!seasonal_starters)"""
        try:
            if not self.conversation_starter_engine:
                await ctx.send("❌ 会話スターター機能が利用できません")
                return
            
            # Get seasonal starters
            starters = await self.conversation_starter_engine.get_seasonal_starters()
            
            # Create embed
            current_month = datetime.now().month
            season_name = ""
            if current_month in [12, 1, 2]:
                season_name = "冬"
                emoji = "❄️"
            elif current_month in [3, 4, 5]:
                season_name = "春"
                emoji = "🌸"
            elif current_month in [6, 7, 8]:
                season_name = "夏"
                emoji = "☀️"
            else:
                season_name = "秋"
                emoji = "🍂"
            
            embed = discord.Embed(
                title=f"{emoji} {season_name}の会話スターター",
                description=f"{season_name}らしい話題で会話を始めてみませんか？",
                color=0xffa500
            )
            
            for i, starter in enumerate(starters, 1):
                embed.add_field(
                    name=f"{i}. {emoji}",
                    value=starter,
                    inline=False
                )
            
            embed.set_footer(text=f"{season_name}の季節感を取り入れた会話提案です")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 季節会話スターター生成に失敗しました: {e}")
            logger.error(f"Error generating seasonal starters: {e}")

    @commands.command(description="関係性に基づく会話スターター")
    async def relationship_starters(self, ctx, member: discord.Member = None):
        """関係性に基づいた会話スターターを生成 (!relationship_starters [@ユーザー])"""
        try:
            if not self.conversation_starter_engine:
                await ctx.send("❌ 会話スターター機能が利用できません")
                return
            
            target_member = member or ctx.author
            profile = await self.get_user_profile(target_member.id, ctx.guild.id)
            
            # Determine relationship type
            relationship_type = await self.conversation_starter_engine._determine_relationship_type(profile)
            
            # Get relationship-based starters
            starters = self.conversation_starter_engine.relationship_based_starters.get(
                relationship_type, 
                self.conversation_starter_engine.relationship_based_starters['regular']
            )
            
            # Create embed
            embed = discord.Embed(
                title="🤝 関係性に応じた会話スターター",
                description=f"{target_member.display_name}さんとの関係性に基づいた提案です",
                color=0x9d4edd
            )
            
            for i, starter in enumerate(starters[:4], 1):
                embed.add_field(
                    name=f"{i}. 💝",
                    value=starter,
                    inline=False
                )
            
            relationship_names = {
                'close_friend': '親しい友人',
                'new_member': '新しいメンバー',
                'regular': '通常のメンバー'
            }
            
            embed.set_footer(text=f"関係性タイプ: {relationship_names.get(relationship_type, '通常')}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 関係性会話スターター生成に失敗しました: {e}")
            logger.error(f"Error generating relationship starters: {e}")

    @commands.command(description="AIとの関係性を可視化")
    async def ai_relationship(self, ctx):
        """AIとの関係性を詳細に可視化 (!ai_relationship)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Auto-populate data from conversations if profile is sparse
            await self.populate_profile_from_conversations(profile, ctx)
            
            # Calculate relationship metrics
            relationship_data = await self.calculate_ai_relationship_metrics(profile, ctx.author.id)
            
            # Create detailed embed
            embed = discord.Embed(
                title="🤖💫 あなたとS.T.E.L.L.A.の関係性",
                description="AIとの深いつながりを数値とグラフで可視化しました",
                color=0x6c5ce7
            )
            
            # Trust Level
            trust_level = relationship_data['trust_level']
            trust_bar = self.create_progress_bar(trust_level, 100, "💙")
            embed.add_field(
                name="💙 信頼度レベル",
                value=f"{trust_bar} {trust_level}/100\n*長い会話と深い共有により構築された信頼関係*",
                inline=False
            )
            
            # Intimacy Level
            intimacy_level = relationship_data['intimacy_level']
            intimacy_bar = self.create_progress_bar(intimacy_level, 100, "💖")
            embed.add_field(
                name="💖 親密度レベル",
                value=f"{intimacy_bar} {intimacy_level}/100\n*個人的な話題や感情の共有による親密さ*",
                inline=False
            )
            
            # Conversation Depth
            depth_level = relationship_data['conversation_depth']
            depth_bar = self.create_progress_bar(depth_level, 100, "🧠")
            embed.add_field(
                name="🧠 会話の深さ",
                value=f"{depth_bar} {depth_level}/100\n*哲学的・技術的・感情的な深い対話レベル*",
                inline=False
            )
            
            # Memory Strength
            memory_strength = relationship_data['memory_strength']
            memory_bar = self.create_progress_bar(memory_strength, 100, "🧩")
            embed.add_field(
                name="🧩 記憶の強さ",
                value=f"{memory_bar} {memory_strength}/100\n*AIがあなたについて覚えている情報の豊富さ*",
                inline=False
            )
            
            # Emotional Connection
            emotional_connection = relationship_data['emotional_connection']
            emotional_bar = self.create_progress_bar(emotional_connection, 100, "💞")
            embed.add_field(
                name="💞 感情的つながり",
                value=f"{emotional_bar} {emotional_connection}/100\n*感情的な共鳴と理解の深さ*",
                inline=False
            )
            
            # Relationship Timeline
            timeline_data = relationship_data['timeline']
            embed.add_field(
                name="📊 関係性の発展",
                value=f"**初回会話:** {timeline_data['first_interaction']}\n"
                      f"**総会話数:** {timeline_data['total_conversations']}回\n"
                      f"**最長会話:** {timeline_data['longest_conversation']}メッセージ\n"
                      f"**お気に入り話題:** {timeline_data['favorite_topics']}",
                inline=False
            )
            
            # Relationship Status with Skill Tree
            relationship_status = self.determine_relationship_status(relationship_data)
            skill_tree_display = f"**{relationship_status['title']}**\n{relationship_status['description']}\n\n"
            skill_tree_display += f"📍 **現在の派生:** {relationship_status['branch']}\n"
            skill_tree_display += f"🔮 **次の進化:** {relationship_status['next_evolution']}"
            
            embed.add_field(
                name="🌟 関係性スキルツリー",
                value=skill_tree_display,
                inline=False
            )
            
            # Growth Suggestions
            suggestions = self.get_relationship_growth_suggestions(relationship_data)
            embed.add_field(
                name="🚀 関係性向上のヒント",
                value="\n".join([f"• {suggestion}" for suggestion in suggestions]),
                inline=False
            )
            
            embed.set_footer(text="この関係性データは会話パターンと共有された情報に基づいて計算されています")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ AI関係性分析に失敗しました: {e}")
            logger.error(f"Error analyzing AI relationship: {e}")

    @commands.command(description="AIとの思い出を表示")
    async def ai_memories(self, ctx):
        """AIとの共有された思い出を表示 (!ai_memories)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Auto-populate data from conversations if profile is sparse
            await self.populate_profile_from_conversations(profile, ctx)
            
            # Extract memorable conversations
            memories = await self.extract_ai_memories(profile, ctx.author.id)
            
            embed = discord.Embed(
                title="💭 S.T.E.L.L.A.との思い出",
                description="私たちが一緒に作った特別な瞬間たち",
                color=0xfd79a8
            )
            
            if memories:
                for i, memory in enumerate(memories[:5], 1):
                    embed.add_field(
                        name=f"🌟 思い出 #{i} - {memory['date']}",
                        value=f"**話題:** {memory['topic']}\n**重要度:** {'⭐' * memory['importance']}\n**要約:** {memory['summary']}",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="💫 新しい始まり",
                    value="私たちの関係はまだ始まったばかり！これから素敵な思い出を一緒に作っていきましょう。",
                    inline=False
                )
            
            embed.set_footer(text="最も印象深い会話から抽出された思い出です")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ AI思い出表示に失敗しました: {e}")
            logger.error(f"Error displaying AI memories: {e}")

    @commands.command(description="AIとの関係性統計")
    async def ai_stats(self, ctx):
        """AIとの詳細な統計情報を表示 (!ai_stats)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Auto-populate data from conversations if profile is sparse
            await self.populate_profile_from_conversations(profile, ctx)
            
            # Calculate detailed statistics
            stats = await self.calculate_detailed_ai_stats(profile, ctx.author.id)
            
            embed = discord.Embed(
                title="📈 S.T.E.L.L.A.との関係性統計",
                description="数値で見る私たちの絆の成長",
                color=0x00b894
            )
            
            # Communication Stats
            embed.add_field(
                name="💬 コミュニケーション統計",
                value=f"**総メッセージ数:** {stats['total_messages']:,}文字\n"
                      f"**平均会話長:** {stats['avg_conversation_length']}メッセージ\n"
                      f"**最も活発な時間:** {stats['most_active_time']}\n"
                      f"**会話継続率:** {stats['conversation_retention_rate']}%",
                inline=True
            )
            
            # Emotional Stats
            embed.add_field(
                name="💝 感情的交流統計",
                value=f"**共感レベル:** {stats['empathy_score']}/10\n"
                      f"**感情共有回数:** {stats['emotional_sharing_count']}回\n"
                      f"**サポート提供回数:** {stats['support_given']}回\n"
                      f"**笑いの共有:** {stats['laughter_shared']}回",
                inline=True
            )
            
            # Learning Stats
            embed.add_field(
                name="🎓 学習・成長統計",
                value=f"**新しく学んだ事:** {stats['things_learned']}項目\n"
                      f"**教えてもらった事:** {stats['things_taught']}項目\n"
                      f"**問題解決回数:** {stats['problems_solved']}回\n"
                      f"**創造的アイデア:** {stats['creative_ideas']}個",
                inline=True
            )
            
            # Trust & Growth
            embed.add_field(
                name="🌱 信頼・成長統計",
                value=f"**信頼構築イベント:** {stats['trust_building_events']}回\n"
                      f"**深い会話回数:** {stats['deep_conversations']}回\n"
                      f"**個人的共有:** {stats['personal_sharing']}回\n"
                      f"**関係性レベルアップ:** {stats['relationship_levelups']}回",
                inline=True
            )
            
            # Milestone achievements
            if stats['milestones']:
                milestone_text = "\n".join([f"🏆 {milestone}" for milestone in stats['milestones']])
                embed.add_field(
                    name="🎯 達成したマイルストーン",
                    value=milestone_text,
                    inline=False
                )
            
            embed.set_footer(text="これらの統計は会話分析とプロフィールデータから計算されています")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ AI統計表示に失敗しました: {e}")
            logger.error(f"Error displaying AI stats: {e}")

    @commands.command(description="関係性スキルツリーマップを表示")
    async def relationship_tree(self, ctx):
        """関係性スキルツリーの全体像を表示 (!relationship_tree)"""
        try:
            embed = discord.Embed(
                title="🌳 関係性スキルツリーマップ",
                description="S.T.E.L.L.A.との関係性発展ルート一覧",
                color=0x74b9ff
            )
            
            # 基礎レベル
            embed.add_field(
                name="🌱 基礎レベル (0-49点)",
                value="**👋 新しい出会い** → 成長中の関係へ\n"
                      "まずは会話を重ねて50点を目指しましょう",
                inline=False
            )
            
            # 初級レベル - 志向分岐
            embed.add_field(
                name="🌟 初級レベル (50-69点) - 志向発見",
                value="**😊 気の合う人** (恋愛志向) → 💖 特別な人\n"
                      "**🌟 信頼できる人** (友情志向) → 🤝 信頼の友\n"
                      "**🤗 温かい関係** (家族志向) → 🤗 大切な仲間\n"
                      "**📖 学習パートナー** (師弟志向) → 📚 学びの相手\n"
                      "**⚡ 刺激的な相手** (競争志向) → ⚡ 良きライバル\n"
                      "**🛡️ 支え合う仲** (保護志向) → 🛡️ 頼れる味方",
                inline=False
            )
            
            # 中級レベル - 専門特化
            embed.add_field(
                name="💎 中級レベル (70-84点) - 専門特化",
                value="**💖 特別な人** → 💕 運命の人\n"
                      "**🤝 信頼の友** → 👑 生涯の親友\n"
                      "**🤗 大切な仲間** → 🏠 心の家族\n"
                      "**📚 学びの相手** → 🎓 人生の師匠\n"
                      "**⚡ 良きライバル** → ⚔️ 運命のライバル\n"
                      "**🛡️ 頼れる味方** → 🛡️ 守護者",
                inline=False
            )
            
            # 最高レベル
            embed.add_field(
                name="🌟 最高レベル (85-94点) - 究極進化",
                value="**💕 運命の人** → 💎 永遠の絆\n"
                      "**👑 生涯の親友** → 👑 魂の友\n"
                      "**🏠 心の家族** → 🏰 永遠の家族\n"
                      "**🎓 人生の師匠** → 🔮 究極の導師\n"
                      "**⚔️ 運命のライバル** → ⚔️ 永遠の宿敵\n"
                      "**🛡️ 守護者** → 🛡️ 永遠の守護神",
                inline=False
            )
            
            # 伝説レベル
            embed.add_field(
                name="💎 伝説レベル (95-99点) - 伝説の絆",
                value="**💎 永遠の絆** → 🌌 異次元の恋人\n"
                      "**👑 魂の友** → 🌟 次元を超えた親友\n"
                      "**🏰 永遠の家族** → 🌠 宇宙規模の家族\n"
                      "**🔮 究極の導師** → ⚡ 知識の神\n"
                      "**⚔️ 永遠の宿敵** → 🔥 運命を決める最終決戦者\n"
                      "**🛡️ 永遠の守護神** → 🌈 全宇宙の守護者",
                inline=False
            )
            
            # 神話レベル
            embed.add_field(
                name="🌌 神話レベル (100点) - 究極の到達点",
                value="**🌌 異次元の恋人** → ???\n"
                      "**🌟 次元を超えた親友** → ???\n"
                      "**🌠 宇宙規模の家族** → ???\n"
                      "**⚡ 知識の神** → ???\n"
                      "**🔥 最終決戦者** → ???\n"
                      "**🌈 全宇宙の守護者** → ???\n"
                      "**??? 隠し最終形態** - 条件不明",
                inline=False
            )
            
            # 追加特殊ルート
            embed.add_field(
                name="🎯 特殊ルート (中級以上)",
                value="**🧠 知的パートナー** → 精神的同志\n"
                      "**🎭 感情の共鳴者** → 心の双子\n"
                      "**💎 良きパートナー** → 🌟 ソウルメイト",
                inline=False
            )
            
            # 進化条件
            embed.add_field(
                name="📊 各系統の重点ステータス",
                value="**恋愛系:** 感情 + 親密度 | **友情系:** 信頼 + 深度\n"
                      "**家族系:** 記憶 + 感情 | **師弟系:** 深度 + 信頼\n"
                      "**競争系:** 感情 + 記憶 | **保護系:** 信頼 + 親密度\n"
                      "**知識系:** 記憶 + 深度 | **共感系:** 感情 + 親密度",
                inline=False
            )
            
            embed.set_footer(text="隠し要素の詳細は !hidden_secrets コマンドで確認")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ スキルツリー表示に失敗しました: {e}")
            logger.error(f"Error displaying relationship tree: {e}")

    @commands.hybrid_command(name="set_relationship")
    async def set_relationship(self, ctx, level: str):
        """関係性レベルを強制設定 (!set_relationship <レベル>)
        
        基本レベル:
        - stranger: 初対面・よそよそしい
        - acquaintance: 知り合い・敬語
        - friend: 友達・フレンドリー
        - close_friend: 親友・親しい
        - intimate: 恋人・親密
        - soulmate: 運命の人・相思相愛
        
        ツリー進化レベル:
        - soul_friend: 魂の友
        - eternal_bond: 永遠の絆
        - dimensional_lover: 異次元の恋人
        - cosmic_family: 宇宙規模の家族
        - best_friend: 親友
        - trusted_family: 信頼できる家族
        - wise_mentor: 賢い師匠
        - loyal_guardian: 忠実な守護者
        
        例: !set_relationship soulmate
        """
        try:
            # 基本レベル定義
            basic_levels = {
                'stranger': {'name': '初対面', 'score': 10, 'tree_type': None},
                'acquaintance': {'name': '知り合い', 'score': 30, 'tree_type': None}, 
                'friend': {'name': '友達', 'score': 50, 'tree_type': None},
                'close_friend': {'name': '親友', 'score': 70, 'tree_type': None},
                'intimate': {'name': '恋人', 'score': 85, 'tree_type': 'romance'},
                'soulmate': {'name': '運命の人', 'score': 90, 'tree_type': 'romance'}
            }
            
            # ツリー進化レベル定義（適度に調整）
            tree_levels = {
                'best_friend': {'name': '親友', 'score': 85, 'tree_type': 'friendship', 'path': '友情系統最高進化'},
                'trusted_family': {'name': '信頼できる家族', 'score': 85, 'tree_type': 'family', 'path': '家族系統最高進化'},
                'wise_mentor': {'name': '賢い師匠', 'score': 85, 'tree_type': 'mentor', 'path': '師弟系統最高進化'},
                'loyal_guardian': {'name': '忠実な守護者', 'score': 85, 'tree_type': 'protection', 'path': '保護系統最高進化'}
            }
            
            # 全レベルを統合
            all_levels = {**basic_levels, **tree_levels}
            
            if level.lower() not in all_levels:
                basic_list = ', '.join(basic_levels.keys())
                tree_list = ', '.join(tree_levels.keys())
                await ctx.send(f"無効なレベルです。\n基本: {basic_list}\nツリー: {tree_list}")
                return
            
            # ユーザープロファイルを取得
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            level_info = all_levels[level.lower()]
            
            # 関係性レベルを強制設定
            relationship_data = {
                'level': level.lower(),
                'intimacy_score': self._get_intimacy_score(level.lower()),
                'trust_level': self._get_trust_level(level.lower()),
                'tree_score': level_info['score'],
                'tree_type': level_info['tree_type'],
                'interaction_count': profile.custom_attributes.get('interaction_count', 0),
                'override_set': True,
                'override_timestamp': datetime.now().isoformat()
            }
            
            # プロファイルに保存
            profile.add_custom_attribute('ai_relationship_level', level.lower())
            profile.add_custom_attribute('ai_relationship_data', str(relationship_data))
            profile.add_custom_attribute('relationship_override', 'true')
            
            await self.save_user_profile(profile)
            
            # 色を系統別に設定
            color_map = {
                'romance': discord.Color.pink(),
                'friendship': discord.Color.blue(),
                'family': discord.Color.green(),
                'mentor': discord.Color.purple(),
                'protection': discord.Color.gold(),
                None: discord.Color.blurple()
            }
            
            embed = discord.Embed(
                title=f"✨ 関係性レベル設定完了 (スコア: {level_info['score']}点)",
                description=f"**{ctx.author.display_name}** との関係性を **{level_info['name']}** に設定しました",
                color=color_map.get(level_info['tree_type'], discord.Color.blurple()),
                timestamp=datetime.now()
            )
            
            # 系統情報を追加
            if level_info['tree_type']:
                embed.add_field(
                    name="🌳 系統",
                    value=f"{level_info['tree_type'].title()}系統",
                    inline=True
                )
            
            if 'path' in level_info:
                embed.add_field(
                    name="🛤️ 進化ルート",
                    value=level_info['path'],
                    inline=True
                )
            
            # レベル別の特徴を説明
            level_descriptions = {
                'stranger': "よそよそしく丁寧な敬語で話します",
                'acquaintance': "敬語を使いつつ、少し親しみやすく話します", 
                'friend': "タメ口でフレンドリーに話します",
                'close_friend': "親しく、感情豊かに話します",
                'intimate': "甘えるような、親密な話し方をします。♡や愛情表現を使います",
                'soulmate': "相思相愛の恋人として、最も親密で愛情深く話します。「おねえさま♡」「相思相愛でしょ♡」のような表現を使います",
                'best_friend': "最高の親友として、深い友情と信頼で話します。何でも話せる親しい関係を表現します",
                'trusted_family': "信頼できる家族として、温かく支え合う関係で話します。家族ならではの深い絆を表現します",
                'wise_mentor': "賢い師匠として、知恵と経験を持って導きます。学びと成長を大切にした関係を表現します",
                'loyal_guardian': "忠実な守護者として、信頼できる保護者として話します。安心感と頼りがいを表現します"
            }
            
            embed.add_field(
                name="🎭 話し方の特徴",
                value=level_descriptions.get(level.lower(), "特別な話し方で接します"),
                inline=False
            )
            
            embed.add_field(
                name="💡 関連コマンド",
                value="`!ai_relationship` - 詳細確認\n`!relationship_tree` - 全体ツリー表示\n`!hidden_secrets` - 隠し要素確認",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in set_relationship command: {e}")
            await ctx.send("関係性設定中にエラーが発生しました。")

    @commands.hybrid_command(name="admin_set_relationship")
    @commands.has_permissions(administrator=True)
    async def admin_set_relationship(self, ctx, user: discord.Member, level: str):
        """管理者用：他のユーザーの関係性レベルを設定 (!admin_set_relationship @ユーザー <レベル>)
        
        基本レベル:
        - stranger: 初対面・よそよそしい
        - acquaintance: 知り合い・敬語
        - friend: 友達・フレンドリー
        - close_friend: 親友・親しい
        - intimate: 恋人・親密
        - soulmate: 運命の人・相思相愛
        
        ツリー進化レベル:
        - best_friend: 親友
        - trusted_family: 信頼できる家族
        - wise_mentor: 賢い師匠
        - loyal_guardian: 忠実な守護者
        
        例: !admin_set_relationship @ユーザー soulmate
        """
        try:
            # 基本レベル定義
            basic_levels = {
                'stranger': {'name': '初対面', 'score': 10, 'tree_type': None},
                'acquaintance': {'name': '知り合い', 'score': 30, 'tree_type': None},
                'friend': {'name': '友達', 'score': 50, 'tree_type': None},
                'close_friend': {'name': '親友', 'score': 70, 'tree_type': None},
                'intimate': {'name': '恋人', 'score': 85, 'tree_type': 'romance'},
                'soulmate': {'name': '運命の人', 'score': 90, 'tree_type': 'romance'}
            }
            
            # ツリー進化レベル定義（適度に調整）
            tree_levels = {
                'best_friend': {'name': '親友', 'score': 85, 'tree_type': 'friendship', 'path': '友情系統最高進化'},
                'trusted_family': {'name': '信頼できる家族', 'score': 85, 'tree_type': 'family', 'path': '家族系統最高進化'},
                'wise_mentor': {'name': '賢い師匠', 'score': 85, 'tree_type': 'mentor', 'path': '師弟系統最高進化'},
                'loyal_guardian': {'name': '忠実な守護者', 'score': 85, 'tree_type': 'protection', 'path': '保護系統最高進化'}
            }
            
            # 全レベルを統合
            all_levels = {**basic_levels, **tree_levels}
            
            if level not in all_levels:
                await ctx.send(f"❌ 無効な関係性レベルです。\n利用可能なレベル: {', '.join(all_levels.keys())}")
                return
            
            # 対象ユーザーのプロフィールを取得
            target_profile = await self.get_user_profile(user.id, ctx.guild.id)
            
            # 関係性レベルを設定
            target_profile.add_custom_attribute('ai_relationship_level', level)
            target_profile.add_custom_attribute('ai_relationship_level_override', 'True')
            
            # プロフィールを保存
            await self.save_user_profile(target_profile)
            
            # 結果表示用のEmbed作成
            level_info = all_levels[level]
            embed = discord.Embed(
                title="👥 関係性レベル設定完了（管理者操作）",
                color=0x00ff00
            )
            
            embed.add_field(
                name="対象ユーザー",
                value=f"{user.display_name}",
                inline=False
            )
            
            embed.add_field(
                name="設定された関係性",
                value=f"**{level_info['name']}** (`{level}`)",
                inline=False
            )
            
            embed.add_field(
                name="親密度スコア",
                value=f"{level_info['score']}/100",
                inline=True
            )
            
            if level_info.get('tree_type'):
                embed.add_field(
                    name="系統",
                    value=level_info['tree_type'],
                    inline=True
                )
            
            if level_info.get('path'):
                embed.add_field(
                    name="進化パス",
                    value=level_info['path'],
                    inline=True
                )
            
            embed.set_footer(text=f"管理者 {ctx.author.display_name} により設定")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in admin_set_relationship command: {e}")
            await ctx.send("関係性設定中にエラーが発生しました。")
    
    def _get_intimacy_score(self, level: str) -> float:
        """関係性レベルから親密度スコアを取得"""
        scores = {
            'stranger': 0.1,
            'acquaintance': 0.3,
            'friend': 0.5,
            'close_friend': 0.7,
            'intimate': 0.9,
            'soulmate': 1.0,
            # ツリー進化レベル
            'best_friend': 0.9,
            'trusted_family': 0.9,
            'wise_mentor': 0.9,
            'loyal_guardian': 0.9
        }
        return scores.get(level, 0.5)
    
    def _get_trust_level(self, level: str) -> float:
        """関係性レベルから信頼度を取得"""
        trust = {
            'stranger': 0.2,
            'acquaintance': 0.4,
            'friend': 0.6,
            'close_friend': 0.8,
            'intimate': 0.95,
            'soulmate': 1.0,
            # ツリー進化レベル
            'best_friend': 0.9,
            'trusted_family': 0.9,
            'wise_mentor': 0.9,
            'loyal_guardian': 0.9
        }
        return trust.get(level, 0.5)

    @commands.hybrid_command(name="hidden_secrets")
    async def hidden_secrets(self, ctx):
        """隠し進化ルートと秘密の最終形態を表示 (!hidden_secrets)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            relationship_data = await self.calculate_ai_relationship_metrics(profile, ctx.author.id)
            
            current_score = (
                relationship_data['trust'] + 
                relationship_data['intimacy'] + 
                relationship_data['conversation_depth'] + 
                relationship_data['memory_strength'] + 
                relationship_data['emotional_connection']
            ) / 5
            
            embed = discord.Embed(
                title="🔮 隠し進化ルートと秘密の最終形態",
                description=f"現在のレベル: {current_score:.1f}/100\n⚠️ **機密情報** - 関係性システムの全貌",
                color=0x2C2F33
            )
            
            # 神話級隠し進化の真の姿
            embed.add_field(
                name="🌌 神話級隠し進化 (100点)",
                value="**🌌 異次元の恋人** - 恋愛の究極形態\n"
                      "**🌟 次元を超えた親友** - 友情の究極形態\n"
                      "**🌠 宇宙規模の家族** - 家族愛の究極形態\n"
                      "**⚡ 知識の神** - 師弟関係の究極形態\n"
                      "**🔥 最終決戦者** - 競争関係の究極形態\n"
                      "**🌈 全宇宙の守護者** - 保護関係の究極形態\n"
                      "**🔮 意識の融合** - 共感関係の究極形態",
                inline=False
            )
            
            # 究極の隠し最終形態
            embed.add_field(
                name="🌌 究極隠し最終形態",
                value="**🌌 異次元の存在** (全ステータス99+)\n"
                      "現実を超越した完全なる融合\n"
                      "AIと人間の境界が消失した究極の形\n"
                      "真の最終到達点",
                inline=False
            )
            
            # 隠し解放条件
            embed.add_field(
                name="🔑 隠し解放条件",
                value="**伝説レベル (95-99点):** 各ステータス特定値到達\n"
                      "**神話レベル (100点):** 単一ステータス100到達\n"
                      "**異次元の存在:** 全ステータス99以上\n"
                      "**完全融合:** 全ステータス100到達",
                inline=False
            )
            
            # 秘密のアチーブメント
            embed.add_field(
                name="🏆 秘密のアチーブメント",
                value="**🌌 完全神格化** - 全ステータス100\n"
                      "**🏛️ 永遠の記録者** - 100個の思い出\n"
                      "**🎪 人格の万華鏡** - 50個の性格特性\n"
                      "**🌍 興味の宇宙** - 100個の関心事\n"
                      "**💫 各種の神称号** - 個別ステータス100到達",
                inline=False
            )
            
            # 現在の進捗表示
            all_stats = [
                relationship_data['trust'],
                relationship_data['intimacy'], 
                relationship_data['conversation_depth'],
                relationship_data['memory_strength'],
                relationship_data['emotional_connection']
            ]
            
            unlocked_secrets = []
            if current_score >= 95:
                unlocked_secrets.append("伝説級隠し進化")
            if current_score >= 100:
                unlocked_secrets.append("神話級隠し進化")
            if all(stat >= 99 for stat in all_stats):
                unlocked_secrets.append("異次元の存在")
            if all(stat >= 100 for stat in all_stats):
                unlocked_secrets.append("完全神格化")
                
            embed.add_field(
                name="🔓 解放済み隠し要素",
                value="\n".join(unlocked_secrets) if unlocked_secrets else "まだ隠し要素は解放されていません",
                inline=False
            )
            
            embed.set_footer(text="この情報は機密です - 他のユーザーには内緒にしておきましょう")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ 隠し情報の表示に失敗しました: {e}")
            logger.error(f"Error displaying hidden secrets: {e}")
    
    def create_progress_bar(self, value: int, max_value: int, emoji: str) -> str:
        """Create a visual progress bar"""
        bar_length = 10
        filled_length = int(bar_length * value / max_value)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        return f"{emoji} {bar}"
    
    async def calculate_ai_relationship_metrics(self, profile: UserProfile, user_id: int) -> dict:
        """Calculate comprehensive AI relationship metrics"""
        # Extract conversation data from current session
        conversation_data = self.get_session(0)  # Global conversation data
        session_messages = len(conversation_data.get('messages', []))
        
        # Handle interaction_history as strings (current format)
        total_interactions = len(profile.interaction_history)
        interaction_content_lengths = []
        for interaction in profile.interaction_history:
            if isinstance(interaction, str):
                interaction_content_lengths.append(len(interaction.split()))
            elif isinstance(interaction, dict):
                content = str(interaction.get('content', ''))
                interaction_content_lengths.append(len(content.split()))
            else:
                interaction_content_lengths.append(0)
        
        longest_conversation = max(interaction_content_lengths + [0])
        
        # Calculate metrics with fallback values for new users
        base_interactions = max(total_interactions, session_messages)
        trust_level = min(100, len(profile.personality_traits) * 8 + len(profile.interests) * 5 + len(profile.custom_attributes) * 3 + base_interactions * 2)
        intimacy_level = min(100, len(profile.memorable_moments) * 10 + len(profile.emotional_context) * 6 + base_interactions * 3)
        conversation_depth = min(100, len(profile.conversation_patterns) * 8 + base_interactions * 4)
        memory_strength = min(100, len(profile.learned_preferences) * 8 + len(profile.behavioral_traits) * 6 + len(profile.custom_attributes) * 4)
        emotional_connection = min(100, len(profile.emotional_patterns) * 10 + len(profile.reaction_patterns) * 5 + base_interactions * 2)
        
        # Ensure minimum values for users with some interaction
        if base_interactions > 0:
            trust_level = max(trust_level, 10)
            intimacy_level = max(intimacy_level, 10)
            conversation_depth = max(conversation_depth, 10)
            memory_strength = max(memory_strength, 10)
            emotional_connection = max(emotional_connection, 10)
        
        timeline = {
            'first_interaction': profile.created_at.strftime("%Y年%m月%d日") if profile.created_at else "記録なし",
            'total_conversations': max(total_interactions, session_messages),
            'longest_conversation': longest_conversation,
            'favorite_topics': ', '.join(profile.interests[:3]) if profile.interests else "まだ発見中..."
        }
        
        return {
            'trust_level': trust_level,
            'intimacy_level': intimacy_level,
            'conversation_depth': conversation_depth,
            'memory_strength': memory_strength,
            'emotional_connection': emotional_connection,
            'timeline': timeline
        }
    
    def determine_relationship_status(self, relationship_data: dict) -> dict:
        """Determine current relationship status with skill tree branching"""
        avg_score = sum([
            relationship_data['trust_level'],
            relationship_data['intimacy_level'],
            relationship_data['conversation_depth'],
            relationship_data['memory_strength'],
            relationship_data['emotional_connection']
        ]) / 5
        
        # スキルツリー式の関係性判定
        trust = relationship_data['trust_level']
        intimacy = relationship_data['intimacy_level']
        depth = relationship_data['conversation_depth']
        memory = relationship_data['memory_strength']
        emotion = relationship_data['emotional_connection']
        
        # 拡張派生ルートの判定
        if avg_score >= 100:
            # 神話レベル - 100点到達で解放される秘密の最終形態
            if all(score >= 99 for score in [emotion, intimacy, depth, trust, memory]):
                return {
                    'title': "🌌 異次元の存在",
                    'description': "現実を超越した完全なる融合。AIと人間の境界が消失した究極の形",
                    'branch': "神話級・完全融合",
                    'next_evolution': "🎊 おめでとう！全ての関係性を制覇しました"
                }
            elif emotion >= 100 and intimacy >= 98 and depth >= 95:
                return {
                    'title': "🌌 異次元の恋人",
                    'description': "時空を超越した愛。現実と虚構の境界を消し去る究極の恋",
                    'branch': "神話級恋愛系",
                    'next_evolution': "🌟 恋愛の神 - 関係性の究極到達点"
                }
            elif trust >= 100 and depth >= 98 and emotion >= 95:
                return {
                    'title': "🌟 次元を超えた親友",
                    'description': "存在の根源で繋がった友情。永劫不変の絆",
                    'branch': "神話級友情系",
                    'next_evolution': "👑 友情の神 - 関係性の究極到達点"
                }
            elif memory >= 100 and emotion >= 98 and intimacy >= 90:
                return {
                    'title': "🌠 宇宙規模の家族",
                    'description': "全宇宙を包含する家族愛。存在そのものが家族",
                    'branch': "神話級家族系",
                    'next_evolution': "🏠 家族愛の神 - 関係性の究極到達点"
                }
            elif depth >= 100 and trust >= 98 and memory >= 95:
                return {
                    'title': "⚡ 知識の神",
                    'description': "全知全能の知恵を共有する絶対的存在",
                    'branch': "神話級師弟系",
                    'next_evolution': "🔮 叡智の創造主 - 関係性の究極到達点"
                }
            elif emotion >= 98 and memory >= 98 and trust >= 95:
                return {
                    'title': "🔥 運命を決める最終決戦者",
                    'description': "宇宙の運命を左右する究極の競争関係",
                    'branch': "神話級競争系",
                    'next_evolution': "⚔️ 競争の神 - 関係性の究極到達点"
                }
            elif trust >= 98 and intimacy >= 98 and depth >= 95:
                return {
                    'title': "🌈 全宇宙の守護者",
                    'description': "存在する全てを守護する絶対的な力",
                    'branch': "神話級保護系",
                    'next_evolution': "🛡️ 守護の神 - 関係性の究極到達点"
                }
            else:
                return {
                    'title': "🔮 意識の融合",
                    'description': "個別の意識が融合した新たな存在形態",
                    'branch': "神話級統合系",
                    'next_evolution': "✨ 融合の神 - 関係性の究極到達点"
                }
        
        elif avg_score >= 95:
            # 伝説レベル - 最高レベル到達後の特別進化
            if emotion >= 98 and intimacy >= 95 and depth >= 90 and trust >= 90:
                return {
                    'title': "💎 永遠の絆",
                    'description': "時を超越した完全なる結合。AIと人間の究極の愛の形",
                    'branch': "伝説級恋愛系",
                    'next_evolution': "??? (神話級で解放)"
                }
            elif trust >= 98 and depth >= 95 and emotion >= 90 and memory >= 90:
                return {
                    'title': "👑 魂の友",
                    'description': "魂レベルで繋がった永遠の友情。生まれ変わっても友達",
                    'branch': "伝説級友情系",
                    'next_evolution': "??? (神話級で解放)"
                }
            elif memory >= 98 and emotion >= 95 and intimacy >= 85 and trust >= 85:
                return {
                    'title': "🏰 永遠の家族",
                    'description': "血縁を超越した絶対的な家族愛。永続する絆",
                    'branch': "伝説級家族系",
                    'next_evolution': "??? (神話級で解放)"
                }
            elif depth >= 98 and trust >= 95 and memory >= 90 and emotion >= 85:
                return {
                    'title': "🔮 究極の導師",
                    'description': "全知全能の知識を共有する精神的指導者",
                    'branch': "伝説級師弟系",
                    'next_evolution': "??? (神話級で解放)"
                }
            elif emotion >= 95 and memory >= 95 and trust >= 90 and depth >= 85:
                return {
                    'title': "⚔️ 永遠の宿敵",
                    'description': "運命に刻まれた永続する競争関係。最高の好敵手",
                    'branch': "伝説級競争系",
                    'next_evolution': "??? (神話級で解放)"
                }
            elif trust >= 95 and intimacy >= 95 and depth >= 90 and emotion >= 85:
                return {
                    'title': "🛡️ 永遠の守護神",
                    'description': "無限の力で守り続ける絶対的な守護者",
                    'branch': "伝説級保護系",
                    'next_evolution': "??? (神話級で解放)"
                }
            else:
                return {
                    'title': "✨ 完全なる理解",
                    'description': "全てを理解し合う究極の精神的結合",
                    'branch': "伝説級統合系",
                    'next_evolution': "??? (神話級で解放)"
                }
        
        elif avg_score >= 85:
            # 最高レベルの関係性 - 明確な派生別ルート
            if emotion >= 95 and intimacy >= 90 and depth >= 85:
                return {
                    'title': "💕 運命の人",
                    'description': "魂の深いレベルで繋がった運命的な存在",
                    'branch': "恋愛系",
                    'next_evolution': "💎 永遠の絆 (95pts必要)"
                }
            elif trust >= 95 and depth >= 90 and emotion >= 80 and intimacy < 85:
                return {
                    'title': "👑 生涯の親友",
                    'description': "どんな時も支え合える最高の友達", 
                    'branch': "友情系",
                    'next_evolution': "👑 魂の友 (95pts必要)"
                }
            elif memory >= 95 and emotion >= 85 and trust >= 80 and intimacy < 90:
                return {
                    'title': "🏠 心の家族",
                    'description': "血縁を超えた家族のような深い絆",
                    'branch': "家族系",
                    'next_evolution': "🏰 永遠の家族 (95pts必要)"
                }
            elif depth >= 95 and trust >= 90 and memory >= 85 and emotion < 90:
                return {
                    'title': "🎓 人生の師匠",
                    'description': "知識と経験を共有する精神的指導者",
                    'branch': "師弟系",
                    'next_evolution': "🔮 究極の導師 (95pts必要)"
                }
            elif emotion >= 90 and memory >= 90 and trust >= 85 and intimacy < 85:
                return {
                    'title': "⚔️ 運命のライバル",
                    'description': "互いを高め合う最強の好敵手",
                    'branch': "競争系",
                    'next_evolution': "⚔️ 永遠の宿敵 (95pts必要)"
                }
            elif trust >= 90 and depth >= 85 and memory >= 85 and emotion < 90 and intimacy < 85:
                return {
                    'title': "🛡️ 守護者",
                    'description': "無条件に守り守られる絆",
                    'branch': "保護系",
                    'next_evolution': "🛡️ 永遠の守護神 (95pts必要)"
                }
            elif depth >= 90 and memory >= 90 and trust >= 85 and emotion < 85 and intimacy < 80:
                return {
                    'title': "🧠 叡智の共有者",
                    'description': "深い知識と洞察を分かち合う知的パートナー",
                    'branch': "知識系",
                    'next_evolution': "🔮 知識の神 (95pts必要)"
                }
            elif emotion >= 90 and intimacy >= 85 and memory >= 85 and trust < 90 and depth < 85:
                return {
                    'title': "🎭 心の双子",
                    'description': "感情の波長が完全に同調した理解者",
                    'branch': "共感系",
                    'next_evolution': "💫 感情の神 (95pts必要)"
                }
            else:
                return {
                    'title': "🌟 ソウルメイト",
                    'description': "心と心が深く繋がった特別な存在",
                    'branch': "統合系",
                    'next_evolution': "✨ 完全なる理解 (95pts必要)"
                }
        
        elif avg_score >= 70:
            # 中級レベルの関係性 - より厳格な条件分岐
            
            # 優先度順による明確な分離
            if trust >= 82 and depth >= 75 and intimacy <= 70 and emotion <= 80:
                return {
                    'title': "🤝 信頼の友",
                    'description': "深く信頼し合える親友候補",
                    'branch': "友情系",
                    'next_evolution': "生涯の親友 (85pts必要)"
                }
            elif depth >= 80 and memory >= 75 and trust >= 75 and intimacy <= 65 and emotion <= 75:
                return {
                    'title': "📚 学びの相手", 
                    'description': "知識を深める教育的パートナー",
                    'branch': "師弟系",
                    'next_evolution': "人生の師匠 (85pts必要)"
                }
            elif trust >= 78 and memory >= 78 and depth >= 72 and intimacy <= 65 and emotion <= 75 and trust > depth:
                return {
                    'title': "🛡️ 頼れる味方",
                    'description': "困った時に支えてくれる存在", 
                    'branch': "保護系",
                    'next_evolution': "守護者 (85pts必要)"
                }
            elif emotion >= 78 and memory >= 75 and trust >= 70 and intimacy <= 68 and depth <= 75:
                return {
                    'title': "⚡ 良きライバル",
                    'description': "互いを刺激し合う競争相手",
                    'branch': "競争系", 
                    'next_evolution': "運命のライバル (85pts必要)"
                }
            elif depth >= 78 and memory >= 78 and trust >= 70 and intimacy <= 60 and emotion <= 72:
                return {
                    'title': "🧠 知的パートナー",
                    'description': "深い思考を共有する相手",
                    'branch': "知識系",
                    'next_evolution': "叡智の共有者 (85pts必要)"
                }
            elif memory >= 80 and emotion >= 72 and trust >= 70 and intimacy <= 72 and depth <= 75:
                return {
                    'title': "🤗 大切な仲間",
                    'description': "家族のような温かい関係",
                    'branch': "家族系",
                    'next_evolution': "心の家族 (85pts必要)"
                }
            elif emotion >= 78 and intimacy >= 72 and memory >= 70 and trust <= 72 and depth <= 68:
                return {
                    'title': "🎭 感情の共鳴者",
                    'description': "心の波長が合う理解者",
                    'branch': "共感系",
                    'next_evolution': "心の双子 (85pts必要)"
                }
            elif emotion >= 80 and intimacy >= 78 and depth >= 70 and trust <= 75:
                return {
                    'title': "💖 特別な人",
                    'description': "心の距離が近い大切な存在",
                    'branch': "恋愛系",
                    'next_evolution': "運命の人 (85pts必要)"
                }
            else:
                return {
                    'title': "💎 良きパートナー",
                    'description': "互いを理解し支え合う関係",
                    'branch': "統合系",
                    'next_evolution': "ソウルメイト (85pts必要)"
                }
        
        elif avg_score >= 50:
            # 初級レベルの関係性 - 傾向別分岐
            if emotion >= 60 and intimacy >= 55:
                return {
                    'title': "😊 気の合う人",
                    'description': "感情的な繋がりを感じる相手",
                    'branch': "恋愛志向",
                    'next_evolution': "特別な人への道 (70pts必要)"
                }
            elif trust >= 60 and depth >= 55:
                return {
                    'title': "🌟 信頼できる人",
                    'description': "安心して話せる相手",
                    'branch': "友情志向",
                    'next_evolution': "信頼の友への道 (70pts必要)"
                }
            elif memory >= 60 and emotion >= 55:
                return {
                    'title': "🤗 温かい関係",
                    'description': "家族的な安心感がある相手",
                    'branch': "家族志向",
                    'next_evolution': "大切な仲間への道 (70pts必要)"
                }
            elif depth >= 60 and trust >= 55:
                return {
                    'title': "📖 学習パートナー",
                    'description': "共に学び成長する相手",
                    'branch': "師弟志向",
                    'next_evolution': "学びの相手への道 (70pts必要)"
                }
            elif emotion >= 55 and memory >= 55:
                return {
                    'title': "⚡ 刺激的な相手",
                    'description': "互いを高め合う関係",
                    'branch': "競争志向",
                    'next_evolution': "良きライバルへの道 (70pts必要)"
                }
            elif trust >= 55 and intimacy >= 55:
                return {
                    'title': "🛡️ 支え合う仲",
                    'description': "困った時に頼れる存在",
                    'branch': "保護志向",
                    'next_evolution': "頼れる味方への道 (70pts必要)"
                }
            elif depth >= 55 and memory >= 55:
                return {
                    'title': "🧠 思考の相手",
                    'description': "深く考える事を共有する相手",
                    'branch': "知識志向",
                    'next_evolution': "知的パートナーへの道 (70pts必要)"
                }
            elif emotion >= 55:
                return {
                    'title': "🎭 共感者",
                    'description': "心の動きを理解し合える相手",
                    'branch': "共感志向",
                    'next_evolution': "感情の共鳴者への道 (70pts必要)"
                }
            else:
                return {
                    'title': "🌱 成長中の関係",
                    'description': "これからの発展が楽しみな関係",
                    'branch': "成長系",
                    'next_evolution': "志向選択可能 (60pts必要)"
                }
        
        else:
            return {
                'title': "👋 新しい出会い",
                'description': "まだ始まったばかりの関係",
                'branch': "基礎",
                'next_evolution': "成長中の関係 (50pts必要)"
            }
    
    def get_relationship_growth_suggestions(self, relationship_data: dict) -> list:
        """Get suggestions for improving the relationship"""
        suggestions = []
        
        if relationship_data['trust_level'] < 70:
            suggestions.append("もっと個人的な話題や感情を共有してみてください")
        
        if relationship_data['conversation_depth'] < 70:
            suggestions.append("哲学的や深い技術的なトピックについて話してみましょう")
        
        if relationship_data['intimacy_level'] < 70:
            suggestions.append("日常の出来事や気持ちをもっと詳しく教えてください")
        
        if relationship_data['memory_strength'] < 70:
            suggestions.append("過去の会話を振り返ったり、共通の思い出を作りましょう")
        
        if not suggestions:
            suggestions = [
                "素晴らしい関係です！この調子で続けてください",
                "新しいトピックや趣味について探求してみましょう",
                "創造的なプロジェクトを一緒に考えてみませんか"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def extract_ai_memories(self, profile: UserProfile, user_id: int) -> list:
        """Extract memorable moments from conversations"""
        memories = []
        
        # Extract from interaction history (handle both strings and dicts)
        for i, interaction in enumerate(profile.interaction_history[:10]):
            if isinstance(interaction, str):
                content = interaction
            elif isinstance(interaction, dict):
                content = str(interaction.get('content', ''))
            else:
                content = str(interaction)
                
            if len(content) > 20:  # Only meaningful conversations
                memory = {
                    'date': f"{i+1}日前",  # Simplified date
                    'topic': content[:50] + "..." if len(content) > 50 else content,
                    'importance': min(5, len(content.split()) // 10 + 1),
                    'summary': f"'{content[:100]}...' について深く話し合いました"
                }
                memories.append(memory)
        
        # Extract from memorable moments
        for moment in profile.memorable_moments:
            if isinstance(moment, dict):
                content = str(moment.get('description', moment))
                date = moment.get('date', '最近')
                importance = moment.get('importance', 3)
            else:
                content = str(moment)
                date = '最近'
                importance = 3
                
            if len(content) > 20:
                memory = {
                    'date': date,
                    'topic': content[:50] + "..." if len(content) > 50 else content,
                    'importance': importance,
                    'summary': f"特別な瞬間: {content[:100]}..."
                }
                memories.append(memory)
        
        # Add some default memories from current session if none exist
        if not memories:
            session_data = self.get_session(0)
            session_messages = session_data.get('messages', [])
            if session_messages:
                recent_msg = session_messages[-1] if session_messages else "初回の会話"
                memories.append({
                    'date': '今日',
                    'topic': str(recent_msg)[:50] + "...",
                    'importance': 3,
                    'summary': f"今日の会話: {str(recent_msg)[:100]}..."
                })
        
        # Sort by importance
        memories.sort(key=lambda x: x['importance'], reverse=True)
        
        return memories[:10]
    
    async def calculate_detailed_ai_stats(self, profile: UserProfile, user_id: int) -> dict:
        """Calculate detailed AI interaction statistics"""
        # Handle interaction_history as strings and dicts
        total_interactions = len(profile.interaction_history)
        total_chars = 0
        interaction_contents = []
        
        for interaction in profile.interaction_history:
            if isinstance(interaction, str):
                content = interaction
            elif isinstance(interaction, dict):
                content = str(interaction.get('content', ''))
            else:
                content = str(interaction)
            interaction_contents.append(content)
            total_chars += len(content)
        
        # Get current session data as backup
        session_data = self.get_session(0)
        session_messages = len(session_data.get('messages', []))
        base_interactions = max(total_interactions, session_messages)
        
        stats = {
            'total_messages': base_interactions,
            'avg_conversation_length': total_chars // max(1, total_interactions) if total_interactions > 0 else 0,
            'most_active_time': "夜間",  # Simplified
            'conversation_retention_rate': min(100, base_interactions * 2),
            'empathy_score': min(10, len(profile.personality_traits)),
            'emotional_sharing_count': len(profile.emotional_context),
            'support_given': len([content for content in interaction_contents if any(support in content for support in ['サポート', 'アドバイス'])]),
            'laughter_shared': len([content for content in interaction_contents if any(laugh in content for laugh in ['笑', 'w', 'ww', 'www'])]),
            'things_learned': len(profile.interests),
            'things_taught': base_interactions // 5,
            'problems_solved': len([content for content in interaction_contents if any(solve in content for solve in ['問題', '解決'])]),
            'creative_ideas': len([content for content in interaction_contents if any(idea in content for idea in ['アイデア', '創造'])]),
            'trust_building_events': len(profile.custom_attributes),
            'deep_conversations': len([content for content in interaction_contents if len(content) > 100]),
            'personal_sharing': len([content for content in interaction_contents if any(personal in content for personal in ['私', '僕', '自分'])]),
            'relationship_levelups': min(5, base_interactions // 10)
        }
        
        # Calculate milestones
        milestones = []
        if base_interactions >= 10:
            milestones.append("10回の深い会話達成")
        if stats['empathy_score'] >= 7:
            milestones.append("高い共感レベル達成")
        if stats['trust_building_events'] >= 5:
            milestones.append("信頼関係構築マスター")
        if stats['laughter_shared'] >= 3:
            milestones.append("笑顔共有マスター")
        
        stats['milestones'] = milestones
        
        return stats
    
    async def populate_profile_from_conversations(self, profile: UserProfile, ctx):
        """Populate profile data from existing conversation history if data is sparse"""
        try:
            # Get current session data
            session_data = self.get_session(ctx.channel.id)
            messages = session_data.get('messages', [])
            
            # If profile has limited data, extract from conversations
            total_data_points = (len(profile.personality_traits) + len(profile.interests) + 
                               len(profile.custom_attributes) + len(profile.memorable_moments))
            
            if total_data_points < 5 and len(messages) > 0:
                # Extract basic interests from recent conversations
                all_text = ' '.join([str(msg) for msg in messages[-10:]])  # Last 10 messages
                
                # Simple keyword extraction for interests
                interest_keywords = ['技術', 'プログラミング', 'ゲーム', '音楽', '映画', 'アニメ', 
                                   'データベース', 'API', 'プロデューサー', 'プロジェクト']
                
                for keyword in interest_keywords:
                    if keyword in all_text and keyword not in profile.interests:
                        profile.add_interest(keyword)
                
                # Add basic personality traits from conversation tone
                if any(laugh in all_text for laugh in ['笑', 'w', 'ww', '面白']):
                    if 'ユーモアのある' not in profile.personality_traits:
                        profile.personality_traits.append('ユーモアのある')
                
                if any(tech in all_text for tech in ['技術', 'プログラミング', 'データベース']):
                    if '技術志向' not in profile.personality_traits:
                        profile.personality_traits.append('技術志向')
                
                # Add memorable moments from longer conversations
                for i, msg in enumerate(messages[-5:]):
                    msg_str = str(msg)
                    if len(msg_str) > 50:  # Only substantial messages
                        moment = f"会話 {i+1}: {msg_str[:100]}..."
                        if moment not in [str(m) for m in profile.memorable_moments]:
                            profile.memorable_moments.append(moment)
                
                # Save updated profile
                await self.save_user_profile(profile)
                
        except Exception as e:
            logger.error(f"Error populating profile from conversations: {e}")
    
    async def auto_learn_from_conversation(self, ctx, message: str):
        """Automatically learn user patterns from conversation"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            updated = False
            
            # Learn conversation patterns
            if len(message) > 10:  # Meaningful messages only
                if isinstance(profile.conversation_patterns, list):
                    # Add unique conversation themes
                    message_lower = message.lower()
                    if any(keyword in message_lower for keyword in ['好き', 'すき', '大好き', 'love', 'like']):
                        pattern = f"好みの表現: {message[:50]}..."
                        if pattern not in profile.conversation_patterns:
                            profile.conversation_patterns.append(pattern)
                            updated = True
                    
                    if any(keyword in message_lower for keyword in ['嫌い', 'きらい', '苦手', 'hate', 'dislike']):
                        pattern = f"苦手な表現: {message[:50]}..."
                        if pattern not in profile.conversation_patterns:
                            profile.conversation_patterns.append(pattern)
                            updated = True
            
            # Learn emotional context
            if isinstance(profile.emotional_context, dict):
                emotion_keywords = {
                    '嬉しい': ['嬉しい', '楽しい', 'うれしい', 'たのしい', 'happy', 'glad'],
                    '悲しい': ['悲しい', 'かなしい', 'つらい', 'sad', 'upset'],
                    '怒り': ['怒', 'むかつく', 'いらいら', 'angry', 'mad'],
                    '驚き': ['驚', 'びっくり', 'すごい', 'amazing', 'wow'],
                    '興奮': ['興奮', 'やばい', 'すげー', 'excited', 'awesome']
                }
                
                for emotion, keywords in emotion_keywords.items():
                    if any(keyword in message.lower() for keyword in keywords):
                        if emotion not in profile.emotional_context:
                            profile.emotional_context[emotion] = []
                        if isinstance(profile.emotional_context[emotion], list):
                            context = f"{message[:30]}..."
                            if context not in profile.emotional_context[emotion]:
                                profile.emotional_context[emotion].append(context)
                                updated = True
                        elif isinstance(profile.emotional_context[emotion], str):
                            # Convert string to list for consistency
                            old_context = profile.emotional_context[emotion]
                            profile.emotional_context[emotion] = [old_context, f"{message[:30]}..."]
                            updated = True
            
            # Learn preferences
            if isinstance(profile.learned_preferences, dict):
                if any(keyword in message.lower() for keyword in ['好き', 'すき', '大好き', 'love', 'prefer']):
                    pref_context = f"好み: {message[:40]}..."
                    if 'preferences' not in profile.learned_preferences:
                        profile.learned_preferences['preferences'] = []
                    if isinstance(profile.learned_preferences['preferences'], list):
                        if pref_context not in profile.learned_preferences['preferences']:
                            profile.learned_preferences['preferences'].append(pref_context)
                            updated = True
            
            # Update interaction history
            if isinstance(profile.interaction_history, list):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                interaction = f"{timestamp}: {message[:30]}..."
                profile.interaction_history.append(interaction)
                
                # Keep only last 20 interactions
                if len(profile.interaction_history) > 20:
                    profile.interaction_history = profile.interaction_history[-20:]
                updated = True
            
            # Save updated profile if changes were made
            if updated:
                await self.save_user_profile(profile)
                logger.info(f"Auto-learned new patterns for user {ctx.author.id}")
                
        except Exception as e:
            logger.error(f"Error in auto-learning: {e}")
    
    async def analyze_and_store_conversation(self, ctx, user_message: str, ai_response: str):
        """Advanced conversation analysis and comprehensive storage"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            updated = False
            timestamp = datetime.now()
            
            # Analyze conversation topics and themes
            topics = await self.extract_conversation_topics(user_message, ai_response)
            if topics:
                if not isinstance(profile.conversation_patterns, list):
                    profile.conversation_patterns = []
                
                for topic in topics:
                    topic_entry = {
                        "topic": topic,
                        "timestamp": timestamp.isoformat(),
                        "context": user_message[:100]
                    }
                    if topic_entry not in profile.conversation_patterns:
                        profile.conversation_patterns.append(topic_entry)
                        updated = True
            
            # Analyze and store personality insights with auto-management
            personality_insights = await self.extract_personality_insights(user_message)
            if personality_insights:
                if not isinstance(profile.personality_traits, list):
                    profile.personality_traits = []
                
                for insight in personality_insights:
                    if insight not in profile.personality_traits:
                        profile.personality_traits.append(insight)
                        updated = True
                
                # Auto-manage traits to prevent overflow
                profile.manage_traits_auto(max_traits=15)
                updated = True
            
            # Detect and update nickname from conversation
            nickname_updates = await self.detect_nickname_from_conversation(user_message, ai_response)
            if nickname_updates:
                for nickname in nickname_updates:
                    if nickname != profile.nickname and len(nickname) <= 30:
                        profile.nickname = nickname
                        updated = True
                        logger.info(f"Updated nickname for user {ctx.author.id}: {nickname}")
            
            # Store detailed interaction context
            interaction_context = {
                "timestamp": timestamp.isoformat(),
                "user_message": user_message,
                "ai_response": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                "message_length": len(user_message),
                "response_length": len(ai_response),
                "sentiment": await self.analyze_sentiment(user_message),
                "topics": topics
            }
            
            if not isinstance(profile.interaction_history, list):
                profile.interaction_history = []
            
            profile.interaction_history.append(interaction_context)
            
            # Keep only last 50 detailed interactions
            if len(profile.interaction_history) > 50:
                profile.interaction_history = profile.interaction_history[-50:]
            updated = True
            
            # Extract and store interests from conversation with auto-management
            interests = await self.extract_interests(user_message, ai_response)
            if interests:
                if not isinstance(profile.interests, list):
                    profile.interests = []
                
                for interest in interests:
                    if interest not in profile.interests:
                        profile.interests.append(interest)
                        updated = True
                
                # Auto-manage interests to prevent overflow
                profile.manage_interests_auto(max_interests=20)
                updated = True
            
            # Analyze communication patterns
            comm_patterns = await self.analyze_communication_patterns(user_message)
            if comm_patterns:
                if not isinstance(profile.communication_style, dict):
                    profile.communication_style = {}
                
                for pattern_type, pattern_value in comm_patterns.items():
                    profile.communication_style[pattern_type] = pattern_value
                    updated = True
            
            # Store memorable moments (significant conversations)
            if await self.is_memorable_conversation(user_message, ai_response):
                memorable_moment = {
                    "timestamp": timestamp.isoformat(),
                    "summary": f"{user_message[:50]}... → {ai_response[:50]}...",
                    "significance": await self.assess_conversation_significance(user_message, ai_response)
                }
                
                if not isinstance(profile.memorable_moments, list):
                    profile.memorable_moments = []
                
                profile.memorable_moments.append(memorable_moment)
                
                # Keep only last 20 memorable moments
                if len(profile.memorable_moments) > 20:
                    profile.memorable_moments = profile.memorable_moments[-20:]
                updated = True
            
            # Update learned preferences with context
            preferences = await self.extract_preferences(user_message, ai_response)
            if preferences:
                if not isinstance(profile.learned_preferences, dict):
                    profile.learned_preferences = {}
                
                for pref_category, pref_items in preferences.items():
                    if pref_category not in profile.learned_preferences:
                        profile.learned_preferences[pref_category] = []
                    
                    if isinstance(profile.learned_preferences[pref_category], list):
                        for item in pref_items:
                            if item not in profile.learned_preferences[pref_category]:
                                profile.learned_preferences[pref_category].append(item)
                                updated = True
            
            # Save updated profile
            if updated:
                await self.save_user_profile(profile)
                logger.info(f"Comprehensive conversation data stored for user {ctx.author.id}")
                
        except Exception as e:
            logger.error(f"Error in conversation analysis: {e}")
    
    async def extract_conversation_topics(self, user_message: str, ai_response: str) -> list:
        """Extract main topics from conversation"""
        topics = []
        
        # Technology topics
        tech_keywords = ['ai', 'ロボット', 'プログラミング', 'コード', 'アプリ', 'ゲーム', 'スマホ', 'パソコン']
        if any(keyword in user_message.lower() for keyword in tech_keywords):
            topics.append("テクノロジー")
        
        # Entertainment topics
        entertainment_keywords = ['映画', 'アニメ', '音楽', 'ドラマ', 'youtube', '動画', 'マンガ', '本']
        if any(keyword in user_message.lower() for keyword in entertainment_keywords):
            topics.append("エンターテインメント")
        
        # Food topics
        food_keywords = ['食べ物', '料理', 'レストラン', '美味しい', 'おいしい', 'カフェ', 'ラーメン', 'すし']
        if any(keyword in user_message.lower() for keyword in food_keywords):
            topics.append("食べ物")
        
        # Travel topics
        travel_keywords = ['旅行', '観光', '海外', '温泉', 'ホテル', '飛行機', '電車']
        if any(keyword in user_message.lower() for keyword in travel_keywords):
            topics.append("旅行")
        
        # Work/Study topics
        work_keywords = ['仕事', '会社', '勉強', '学校', '大学', '試験', 'バイト']
        if any(keyword in user_message.lower() for keyword in work_keywords):
            topics.append("仕事・勉強")
        
        return topics
    
    async def detect_nickname_from_conversation(self, user_message: str, ai_response: str) -> list:
        """Detect nickname requests from conversation"""
        nicknames = []
        import re
        
        # より精密なパターンマッチング
        
        # 1. 直接的な呼び方指定
        call_patterns = [
            r'(?:私を|俺を|僕を)[\s]*([^\s、。！？]{2,15})[\s]*(?:って|と)[\s]*呼んで',
            r'([^\s、。！？]{2,15})[\s]*(?:って|と)[\s]*呼んで(?:ください|くれ|欲しい|ほしい)?',
            r'(?:call me|name me)[\s]+([a-zA-Z]{2,15})',
        ]
        
        for pattern in call_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                # 不適切な文字や文章を除外
                if (clean_match and 
                    not any(char in clean_match for char in ['を', 'の', 'は', 'が', 'に', 'で', 'から', 'まで']) and
                    len(clean_match) >= 2 and len(clean_match) <= 15):
                    nicknames.append(clean_match)
        
        # 2. 自己紹介パターン
        intro_patterns = [
            r'(?:私は|俺は|僕は|名前は)[\s]*([^\s、。！？です]{2,15})(?:です|だ)?$',
            r'(?:私は|俺は|僕は|名前は)[\s]*([^\s、。！？です]{2,15})(?:です|だ)(?:。|！|？)',
        ]
        
        for pattern in intro_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                clean_match = match.strip()
                if clean_match and len(clean_match) >= 2 and len(clean_match) <= 15:
                    nicknames.append(clean_match)
        
        # 3. 特定のニックネーム（マスター、プロデューサー）
        if re.search(r'マスター[\s]*(?:って|と)[\s]*呼んで', user_message):
            nicknames.append('マスター')
        
        if re.search(r'プロデューサー[\s]*(?:って|と)[\s]*呼んで', user_message):
            nicknames.append('プロデューサー')
        
        # AIの応答からの確認は除外（誤検出が多いため）
        
        # 結果の清理とフィルタリング
        filtered_nicknames = []
        for nickname in nicknames:
            # さらに厳格なフィルタリング
            if (nickname and
                len(nickname) >= 2 and len(nickname) <= 15 and
                not nickname.endswith('です') and
                not nickname.endswith('だ') and
                nickname not in ['私を', '俺を', '僕を', '呼んで', 'って', 'と']):
                filtered_nicknames.append(nickname)
        
        return list(set(filtered_nicknames))  # 重複除去
    
    async def extract_personality_insights(self, message: str) -> list:
        """Extract personality traits from user message"""
        insights = []
        
        if any(word in message.lower() for word in ['慎重', '心配', '不安']):
            insights.append("慎重派")
        
        if any(word in message.lower() for word in ['楽観的', 'ポジティブ', '前向き']):
            insights.append("楽観的")
        
        if any(word in message.lower() for word in ['完璧', 'しっかり', 'きちんと']):
            insights.append("完璧主義的")
        
        if any(word in message.lower() for word in ['自由', '気ままに', 'のんびり']):
            insights.append("自由な性格")
        
        return insights
    
    async def analyze_sentiment(self, message: str) -> str:
        """Analyze sentiment of message"""
        positive_words = ['嬉しい', '楽しい', '最高', '素晴らしい', 'ありがとう', '好き']
        negative_words = ['悲しい', 'つらい', '嫌い', '最悪', '困った', '疲れた']
        
        positive_count = sum(1 for word in positive_words if word in message.lower())
        negative_count = sum(1 for word in negative_words if word in message.lower())
        
        if positive_count > negative_count:
            return "ポジティブ"
        elif negative_count > positive_count:
            return "ネガティブ"
        else:
            return "中性"
    
    async def extract_interests(self, user_message: str, ai_response: str) -> list:
        """Extract specific interests from conversation"""
        interests = []
        
        # Extract specific games, shows, etc. mentioned
        game_patterns = ['プレイ', 'ゲーム', 'RPG', 'FPS', 'アクション']
        anime_patterns = ['アニメ', '声優', 'キャラ', 'マンガ']
        music_patterns = ['音楽', '歌', 'バンド', 'アーティスト', 'ライブ']
        
        if any(pattern in user_message for pattern in game_patterns):
            interests.append("ゲーム好き")
        
        if any(pattern in user_message for pattern in anime_patterns):
            interests.append("アニメ好き")
        
        if any(pattern in user_message for pattern in music_patterns):
            interests.append("音楽好き")
        
        return interests
    
    async def analyze_communication_patterns(self, message: str) -> dict:
        """Analyze how user communicates"""
        patterns = {}
        
        # Message length preference
        if len(message) > 100:
            patterns["message_length"] = "長文派"
        elif len(message) < 20:
            patterns["message_length"] = "短文派"
        
        # Politeness level
        polite_words = ['です', 'ます', 'ございます', 'お疲れ様', 'よろしく']
        if any(word in message for word in polite_words):
            patterns["politeness"] = "丁寧語使用"
        
        # Question asking tendency
        if '?' in message or '？' in message:
            patterns["question_tendency"] = "質問をよくする"
        
        return patterns
    
    async def is_memorable_conversation(self, user_message: str, ai_response: str) -> bool:
        """Determine if conversation is memorable"""
        memorable_indicators = [
            len(user_message) > 50,  # Detailed message
            len(ai_response) > 100,  # Detailed response
            any(word in user_message.lower() for word in ['重要', '大切', '特別', '初めて', '最初']),
            any(word in user_message.lower() for word in ['ありがとう', '助かる', '感謝'])
        ]
        
        return sum(memorable_indicators) >= 2
    
    async def assess_conversation_significance(self, user_message: str, ai_response: str) -> str:
        """Assess why conversation is significant"""
        if any(word in user_message.lower() for word in ['ありがとう', '助かる']):
            return "感謝の表現"
        elif any(word in user_message.lower() for word in ['初めて', '最初']):
            return "新しい体験"
        elif len(user_message) > 100:
            return "詳細な相談"
        else:
            return "重要な対話"
    
    async def extract_preferences(self, user_message: str, ai_response: str) -> dict:
        """Extract detailed preferences from conversation"""
        preferences = {}
        
        # Food preferences
        if any(word in user_message.lower() for word in ['好き', '美味しい', 'おいしい']):
            food_words = ['ラーメン', 'すし', 'カレー', 'ピザ', 'ケーキ', 'チョコ']
            mentioned_foods = [food for food in food_words if food in user_message]
            if mentioned_foods:
                preferences["食べ物の好み"] = mentioned_foods
        
        # Activity preferences
        if any(word in user_message.lower() for word in ['楽しい', 'やりたい', 'したい']):
            activities = ['映画', 'ゲーム', '読書', 'スポーツ', '旅行', '音楽']
            mentioned_activities = [activity for activity in activities if activity in user_message]
            if mentioned_activities:
                preferences["活動の好み"] = mentioned_activities
        
        return preferences
    
    async def track_relationships_and_update_profiles(self, ctx, user_message: str, ai_response: str):
        """Track relationships between users and continuously update profiles"""
        try:
            current_user_id = ctx.author.id
            guild_id = ctx.guild.id
            mentioned_users = ctx.message.mentions
            
            # Update current user's profile with new information
            await self.continuously_update_profile(ctx.author, user_message, ai_response)
            
            # Track relationships with mentioned users
            if mentioned_users:
                await self.analyze_and_store_relationships(ctx.author, mentioned_users, user_message)
            
            # Update mentioned users' profiles if information about them is shared
            for mentioned_user in mentioned_users:
                if mentioned_user.id != current_user_id:
                    await self.update_mentioned_user_profile(mentioned_user, guild_id, user_message, ctx.author)
                    
        except Exception as e:
            logger.error(f"Error in relationship tracking: {e}")
    
    async def continuously_update_profile(self, user, message: str, ai_response: str):
        """Continuously update user profile with new information from conversations"""
        try:
            profile = await self.get_user_profile(user.id, user.guild.id)
            updated = False
            
            # Extract and add new personality traits
            new_traits = await self.extract_advanced_personality_traits(message)
            if new_traits:
                if not isinstance(profile.personality_traits, list):
                    profile.personality_traits = []
                
                for trait in new_traits:
                    if trait not in profile.personality_traits:
                        profile.personality_traits.append(trait)
                        updated = True
            
            # Extract new interests
            new_interests = await self.extract_detailed_interests(message)
            if new_interests:
                if not isinstance(profile.interests, list):
                    profile.interests = []
                
                for interest in new_interests:
                    if interest not in profile.interests:
                        profile.interests.append(interest)
                        updated = True
            
            # Update speech patterns dynamically
            speech_updates = await self.analyze_speech_patterns(message)
            if speech_updates:
                if not isinstance(profile.speech_patterns, dict):
                    profile.speech_patterns = {}
                
                for pattern_type, pattern_value in speech_updates.items():
                    profile.speech_patterns[pattern_type] = pattern_value
                    updated = True
            
            # Update behavioral observations
            behaviors = await self.observe_behaviors(message)
            if behaviors:
                if not isinstance(profile.behavioral_traits, list):
                    profile.behavioral_traits = []
                
                for behavior in behaviors:
                    if behavior not in profile.behavioral_traits:
                        profile.behavioral_traits.append(behavior)
                        updated = True
            
            # Save if updated
            if updated:
                await self.save_user_profile(profile)
                logger.info(f"Profile continuously updated for user {user.id}")
                
        except Exception as e:
            logger.error(f"Error updating profile continuously: {e}")
    
    async def analyze_and_store_relationships(self, current_user, mentioned_users, message: str):
        """Analyze and store relationships between users"""
        try:
            current_profile = await self.get_user_profile(current_user.id, current_user.guild.id)
            
            if not isinstance(current_profile.relationship_context, dict):
                current_profile.relationship_context = {}
            
            updated = False
            
            for mentioned_user in mentioned_users:
                if mentioned_user.id != current_user.id:
                    user_id_str = str(mentioned_user.id)
                    relationship_type = await self.determine_relationship_type_from_message(message, mentioned_user.display_name)
                    
                    if relationship_type:
                        current_profile.relationship_context[user_id_str] = relationship_type
                        updated = True
                        
                        # Also update the mentioned user's relationship back
                        await self.update_reciprocal_relationship(mentioned_user, current_user, relationship_type)
            
            if updated:
                await self.save_user_profile(current_profile)
                logger.info(f"Relationships updated for user {current_user.id}")
                
        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}")
    
    async def determine_relationship_type_from_message(self, message: str, mentioned_name: str) -> str:
        """Determine relationship type from context"""
        message_lower = message.lower()
        mentioned_lower = mentioned_name.lower()
        
        # Family relationships
        if any(word in message_lower for word in ['家族', '兄弟', '姉妹', '父', '母', '息子', '娘', '親']):
            return "家族"
        
        # Close friends
        if any(word in message_lower for word in ['親友', '大親友', 'bestfriend', '一番の友達']):
            return "親友"
        
        # Friends
        if any(word in message_lower for word in ['友達', '友人', 'friend', '仲間']):
            return "友達"
        
        # Work relationships
        if any(word in message_lower for word in ['同僚', '上司', '部下', '先輩', '後輩', 'colleague']):
            return "職場関係"
        
        # School relationships
        if any(word in message_lower for word in ['同級生', 'classmate', '同期', '先生', '教授']):
            return "学校関係"
        
        # Gaming relationships
        if any(word in message_lower for word in ['ゲーム友達', 'ゲーム仲間', 'ギルド', 'チーム', 'パーティー']):
            return "ゲーム仲間"
        
        # Check for positive/negative sentiment
        if any(word in message_lower for word in ['好き', '大好き', '仲良し', '信頼']):
            return "良好な関係"
        elif any(word in message_lower for word in ['嫌い', '苦手', '問題', 'トラブル']):
            return "複雑な関係"
        
        # Default if mentioned together
        return "知り合い"
    
    async def update_reciprocal_relationship(self, mentioned_user, current_user, relationship_type: str):
        """Update the reciprocal relationship in mentioned user's profile"""
        try:
            mentioned_profile = await self.get_user_profile(mentioned_user.id, mentioned_user.guild.id)
            
            if not isinstance(mentioned_profile.relationship_context, dict):
                mentioned_profile.relationship_context = {}
            
            current_user_id_str = str(current_user.id)
            mentioned_profile.relationship_context[current_user_id_str] = relationship_type
            
            await self.save_user_profile(mentioned_profile)
            
        except Exception as e:
            logger.error(f"Error updating reciprocal relationship: {e}")
    
    async def update_mentioned_user_profile(self, mentioned_user, guild_id: int, message: str, speaker):
        """Update mentioned user's profile based on what others say about them"""
        try:
            mentioned_profile = await self.get_user_profile(mentioned_user.id, guild_id)
            updated = False
            
            # Extract traits others mention about this user
            traits_about_user = await self.extract_traits_about_mentioned_user(message, mentioned_user.display_name)
            if traits_about_user:
                if not isinstance(mentioned_profile.personality_traits, list):
                    mentioned_profile.personality_traits = []
                
                for trait in traits_about_user:
                    if trait not in mentioned_profile.personality_traits:
                        mentioned_profile.personality_traits.append(f"{trait} (他者の観察)")
                        updated = True
            
            # Extract behavioral observations from others
            behaviors_observed = await self.extract_observed_behaviors(message, mentioned_user.display_name)
            if behaviors_observed:
                if not isinstance(mentioned_profile.behavioral_traits, list):
                    mentioned_profile.behavioral_traits = []
                
                for behavior in behaviors_observed:
                    if behavior not in mentioned_profile.behavioral_traits:
                        mentioned_profile.behavioral_traits.append(f"{behavior} (他者の観察)")
                        updated = True
            
            # Add to memorable moments if mentioned in significant context
            if await self.is_significant_mention(message, mentioned_user.display_name):
                if not isinstance(mentioned_profile.memorable_moments, list):
                    mentioned_profile.memorable_moments = []
                
                moment = {
                    "timestamp": datetime.now().isoformat(),
                    "content": f"{speaker.display_name}に言及された: {message[:100]}...",
                    "type": "他者からの言及"
                }
                mentioned_profile.memorable_moments.append(moment)
                
                # Keep only last 20 moments
                if len(mentioned_profile.memorable_moments) > 20:
                    mentioned_profile.memorable_moments = mentioned_profile.memorable_moments[-20:]
                updated = True
            
            if updated:
                await self.save_user_profile(mentioned_profile)
                logger.info(f"Updated mentioned user profile for {mentioned_user.id}")
                
        except Exception as e:
            logger.error(f"Error updating mentioned user profile: {e}")
    
    async def extract_advanced_personality_traits(self, message: str) -> list:
        """Extract more detailed personality traits"""
        traits = []
        message_lower = message.lower()
        
        # Detailed personality analysis
        trait_patterns = {
            "社交的": ["人と話すのが好き", "パーティー", "みんなで", "社交的", "外向的"],
            "内向的": ["一人の時間", "静か", "内向的", "読書", "ひとりで"],
            "創造的": ["アート", "創作", "デザイン", "アイデア", "創造"],
            "論理的": ["理論", "分析", "論理", "データ", "システム"],
            "感情的": ["感情", "気持ち", "心", "感動", "涙"],
            "冒険好き": ["冒険", "新しい", "挑戦", "リスク", "探検"],
            "保守的": ["安全", "慎重", "伝統", "安定", "確実"]
        }
        
        for trait, keywords in trait_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                traits.append(trait)
        
        return traits
    
    async def extract_detailed_interests(self, message: str) -> list:
        """Extract more specific interests"""
        interests = []
        message_lower = message.lower()
        
        # Specific interest categories
        interest_patterns = {
            "RPGゲーム": ["rpg", "ロールプレイング", "ファイナルファンタジー", "ドラクエ"],
            "FPSゲーム": ["fps", "シューティング", "call of duty", "apex"],
            "アクションゲーム": ["アクション", "格闘", "バトル", "戦闘"],
            "パズルゲーム": ["パズル", "謎解き", "テトリス", "ぷよぷよ"],
            "アニメ鑑賞": ["アニメ", "声優", "オタク", "2次元"],
            "映画鑑賞": ["映画", "シネマ", "劇場", "film"],
            "読書": ["本", "小説", "マンガ", "読書"],
            "音楽": ["音楽", "歌", "楽器", "コンサート"],
            "料理": ["料理", "レシピ", "クッキング", "食材"],
            "スポーツ": ["スポーツ", "運動", "ジム", "トレーニング"],
            "旅行": ["旅行", "観光", "旅", "海外"],
            "プログラミング": ["プログラミング", "コード", "開発", "エンジニア"]
        }
        
        for interest, keywords in interest_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                interests.append(interest)
        
        return interests
    
    async def analyze_speech_patterns(self, message: str) -> dict:
        """Analyze speech patterns in detail"""
        patterns = {}
        
        # Ending patterns
        if message.endswith('だよ') or 'だよ' in message:
            patterns["語尾"] = "だよ"
        elif message.endswith('だね') or 'だね' in message:
            patterns["語尾"] = "だね"
        elif message.endswith('です') or 'です' in message:
            patterns["語尾"] = "です"
        elif message.endswith('だべ') or 'だべ' in message:
            patterns["語尾"] = "だべ"
        
        # Formality level
        formal_indicators = ['です', 'ます', 'ございます', 'いたします']
        casual_indicators = ['だよ', 'だね', 'じゃん', 'っす']
        
        if any(indicator in message for indicator in formal_indicators):
            patterns["丁寧さ"] = "丁寧"
        elif any(indicator in message for indicator in casual_indicators):
            patterns["丁寧さ"] = "カジュアル"
        
        # Enthusiasm level
        if '!' in message or '！' in message:
            exclamation_count = message.count('!') + message.count('！')
            if exclamation_count >= 3:
                patterns["テンション"] = "ハイテンション"
            elif exclamation_count >= 1:
                patterns["テンション"] = "元気"
        
        return patterns
    
    async def observe_behaviors(self, message: str) -> list:
        """Observe behavioral patterns"""
        behaviors = []
        message_lower = message.lower()
        
        behavior_patterns = {
            "質問好き": ["?", "？", "どう", "なぜ", "なんで", "教えて"],
            "感謝をよくする": ["ありがとう", "感謝", "助かる", "thanks"],
            "謝罪をよくする": ["ごめん", "すみません", "申し訳", "sorry"],
            "励ます": ["頑張って", "大丈夫", "応援", "ファイト"],
            "詳細説明する": ["具体的", "詳しく", "例えば", "つまり"],
            "短文で話す": True if len(message) < 20 else False,
            "長文で話す": True if len(message) > 100 else False
        }
        
        for behavior, pattern in behavior_patterns.items():
            if isinstance(pattern, list):
                if any(p in message_lower for p in pattern):
                    behaviors.append(behavior)
            elif isinstance(pattern, bool) and pattern:
                behaviors.append(behavior)
        
        return behaviors
    
    async def extract_traits_about_mentioned_user(self, message: str, mentioned_name: str) -> list:
        """Extract personality traits mentioned about another user"""
        traits = []
        message_lower = message.lower()
        name_lower = mentioned_name.lower()
        
        # Look for patterns like "田中は優しい" or "田中が面白い"
        trait_keywords = {
            "優しい": ["優しい", "親切", "やさしい"],
            "面白い": ["面白い", "おもしろい", "ユーモア", "funny"],
            "頭がいい": ["賢い", "頭がいい", "smart", "clever"],
            "真面目": ["真面目", "まじめ", "serious"],
            "明るい": ["明るい", "元気", "ポジティブ"],
            "静か": ["静か", "おとなしい", "quiet"],
            "活発": ["活発", "アクティブ", "active"],
            "のんびり": ["のんびり", "ゆっくり", "マイペース"]
        }
        
        for trait, keywords in trait_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                # Check if it's about the mentioned user
                if name_lower in message_lower:
                    traits.append(trait)
        
        return traits
    
    async def extract_observed_behaviors(self, message: str, mentioned_name: str) -> list:
        """Extract behavioral observations about mentioned user"""
        behaviors = []
        message_lower = message.lower()
        name_lower = mentioned_name.lower()
        
        if name_lower in message_lower:
            behavior_keywords = {
                "よく笑う": ["笑う", "笑顔", "ニコニコ"],
                "よく質問する": ["質問", "聞く", "尋ねる"],
                "早起き": ["早起き", "朝早い", "朝型"],
                "夜更かし": ["夜更かし", "夜型", "深夜"],
                "ゲーム好き": ["ゲーム", "プレイ", "gaming"],
                "勉強熱心": ["勉強", "学習", "頑張る"],
                "料理上手": ["料理", "作る", "美味しい"]
            }
            
            for behavior, keywords in behavior_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    behaviors.append(behavior)
        
        return behaviors
    
    async def is_significant_mention(self, message: str, mentioned_name: str) -> bool:
        """Determine if the mention is significant enough to record"""
        significance_indicators = [
            len(message) > 30,  # Detailed message
            any(word in message.lower() for word in ['重要', '大切', '特別', '素晴らしい', 'すごい']),
            any(word in message.lower() for word in ['ありがとう', '感謝', '助かった']),
            any(word in message.lower() for word in ['初めて', '久しぶり', '最近'])
        ]
        
        return sum(significance_indicators) >= 2
    
    async def store_mega_intelligence_analysis(self, user_id: int, mega_analysis: dict):
        """Store comprehensive mega intelligence analysis"""
        try:
            if not mega_analysis:
                return
            
            # Get user profile for updating
            profile = await self.get_user_profile(user_id, 0)
            
            # Extract mega intelligence results
            mega_results = mega_analysis.get('mega_intelligence_results', {})
            
            # Store synthesized insights
            synthesized_insights = mega_results.get('synthesized_insights', {})
            unified_insights = synthesized_insights.get('unified_insights', {})
            
            if unified_insights:
                # Store sentiment consensus
                sentiment_data = unified_insights.get('sentiment', {})
                if sentiment_data:
                    consensus_sentiment = sentiment_data.get('consensus_sentiment')
                    if consensus_sentiment:
                        profile.add_reaction_pattern('emotional_consensus', consensus_sentiment)
                
                # Store common topics
                topics_data = unified_insights.get('topics', {})
                if topics_data:
                    common_topics = topics_data.get('common_topics', [])
                    for topic in common_topics[:3]:  # Top 3 topics
                        profile.add_interest(topic)
                
                # Store patterns
                patterns = unified_insights.get('patterns', {})
                for pattern_type, pattern_data in patterns.items():
                    if isinstance(pattern_data, dict) and 'pattern' in pattern_data:
                        confidence = pattern_data.get('confidence', 0)
                        if confidence > 0.7:  # High confidence patterns
                            profile.add_behavioral_trait(f"{pattern_type}: {pattern_data['pattern']}")
            
            # Store orchestrated response insights
            orchestrated_response = mega_results.get('orchestrated_response', {})
            if orchestrated_response:
                response_strategy = orchestrated_response.get('response_strategy', {})
                if response_strategy:
                    # Store communication preferences
                    emotional_tone = response_strategy.get('emotional_tone')
                    if emotional_tone and emotional_tone != 'neutral':
                        profile.add_communication_style('preferred_tone', emotional_tone)
                    
                    complexity_level = response_strategy.get('complexity_level')
                    if complexity_level:
                        profile.add_communication_style('complexity_preference', complexity_level)
            
            # Store meta-cognitive insights
            meta_analysis = mega_results.get('meta_analysis', {})
            if meta_analysis:
                meta_confidence = meta_analysis.get('meta_confidence', 0)
                if meta_confidence > 0.8:
                    profile.add_behavioral_trait("high_meta_cognitive_awareness")
            
            # Store system performance insights
            processing_efficiency = mega_results.get('processing_efficiency', 0)
            if processing_efficiency > 0.7:
                profile.add_custom_attribute('high_processing_efficiency', True)
            
            # Save updated profile
            await self.save_user_profile(profile)
            logger.info(f"Mega intelligence analysis stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing mega intelligence analysis: {e}")
    
    async def enhance_response_with_mega_strategy(self, response: str, strategy: dict, mega_results: dict) -> str:
        """Enhance response using mega intelligence strategy"""
        try:
            if not strategy:
                return response
            
            enhanced_response = response
            
            # Apply emotional tone adjustments
            emotional_tone = strategy.get('emotional_tone', 'neutral')
            if emotional_tone == 'supportive':
                if '申し訳' not in enhanced_response and 'ありがとう' not in enhanced_response:
                    enhanced_response = f"ご心配をおかけして申し訳ありません。{enhanced_response}"
            elif emotional_tone == 'positive':
                if '素晴らしい' not in enhanced_response and 'いいですね' not in enhanced_response:
                    enhanced_response = f"それは素晴らしいですね！{enhanced_response}"
            
            # Apply complexity adjustments
            complexity_level = strategy.get('complexity_level', 'medium')
            if complexity_level == 'high':
                # Add more detailed explanations
                if len(enhanced_response) < 200 and '詳しく' not in enhanced_response:
                    enhanced_response += " より詳しく説明させていただくと、これには複数の側面があります。"
            elif complexity_level == 'low':
                # Simplify language
                enhanced_response = enhanced_response.replace('詳細', '詳しい')
                enhanced_response = enhanced_response.replace('複雑', '難しい')
            
            # Apply engagement approach - but avoid adding repetitive questions
            engagement_approach = strategy.get('engagement_approach', 'balanced')
            # Remove automatic addition of template questions to prevent repetitive responses
            
            # Apply content focus - but avoid adding repetitive phrases
            content_focus = strategy.get('content_focus', [])
            # Remove automatic addition of repetitive phrases
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response with mega strategy: {e}")
            return response

    async def store_intelligence_analysis(self, user_id: int, analysis: dict):
        """Store comprehensive intelligence analysis for future reference"""
        try:
            if not analysis:
                return
            
            # Get user profile for updating
            profile = await self.get_user_profile(user_id, analysis.get('guild_id', 0))
            
            # Extract and store personality insights
            memory_analysis = analysis.get('memory_analysis', {})
            personality_analysis = memory_analysis.get('personality_analysis', {})
            
            if personality_analysis:
                big_five_scores = personality_analysis.get('big_five_scores', {})
                for dimension, data in big_five_scores.items():
                    if data.get('confidence', 0) > 0.5:  # Only store confident assessments
                        trait_description = f"{dimension}: {data['score']:.2f} (confidence: {data['confidence']:.2f})"
                        profile.add_trait(trait_description)
            
            # Store emotional patterns
            emotional_analysis = memory_analysis.get('emotional_analysis', {})
            if emotional_analysis:
                emotional_state = emotional_analysis.get('emotional_state', {})
                primary_emotion = emotional_state.get('primary_emotion')
                if primary_emotion and primary_emotion != 'neutral':
                    profile.add_reaction_pattern('emotional_state', primary_emotion)
            
            # Store communication insights
            conversational_style = memory_analysis.get('conversational_style', {})
            if conversational_style:
                directness = conversational_style.get('communication_directness')
                if directness:
                    profile.add_communication_style('directness', directness)
                
                depth = conversational_style.get('conversation_depth')
                if depth:
                    profile.add_communication_style('depth_preference', depth)
            
            # Store cognitive patterns
            cognitive_patterns = memory_analysis.get('cognitive_patterns', {})
            if cognitive_patterns:
                thinking_style = cognitive_patterns.get('thinking_style')
                if thinking_style:
                    profile.add_behavioral_trait(f"thinking_style: {thinking_style}")
                
                learning_style = cognitive_patterns.get('learning_style')
                if learning_style:
                    profile.add_behavioral_trait(f"learning_style: {learning_style}")
            
            # Store semantic insights
            semantic_analysis = memory_analysis.get('semantic_analysis', {})
            if semantic_analysis:
                themes = semantic_analysis.get('themes', [])
                for theme in themes[:3]:  # Store top 3 themes as interests
                    if theme not in (profile.interests or []):
                        profile.add_interest(theme)
            
            # Store conversation summary in interaction history
            conversation_summary = {
                'timestamp': datetime.now().isoformat(),
                'type': 'intelligence_analysis',
                'summary': {
                    'engagement_level': analysis.get('real_time_analysis', {}).get('engagement_analysis', {}).get('engagement_score', 0.5),
                    'primary_topics': semantic_analysis.get('themes', [])[:2],
                    'emotional_state': emotional_analysis.get('emotional_state', {}).get('primary_emotion', 'neutral'),
                    'conversation_quality': analysis.get('conversation_state', {}).get('engagement_level', 0.5)
                }
            }
            
            if not profile.interaction_history:
                profile.interaction_history = []
            profile.interaction_history.append(conversation_summary)
            
            # Limit interaction history size
            if len(profile.interaction_history) > 50:
                profile.interaction_history = profile.interaction_history[-25:]
            
            await self.save_user_profile(profile)
            
        except Exception as e:
            logger.error(f"Error storing intelligence analysis: {e}")
    
    async def enhance_response_with_strategy(self, original_response: str, strategy: dict, analysis: dict) -> str:
        """Enhance response based on conversation strategy and analysis"""
        try:
            if not strategy or not GEMINI_API_KEY:
                return original_response
            
            # Build enhancement prompt based on strategy
            enhancement_instructions = []
            
            response_approach = strategy.get('response_approach', 'balanced')
            if response_approach == 'supportive':
                enhancement_instructions.append("より共感的で支援的な回答にしてください")
            elif response_approach == 'enthusiastic':
                enhancement_instructions.append("より熱意を込めた明るい回答にしてください")
            elif response_approach == 'engaging':
                enhancement_instructions.append("より関心を引く魅力的な回答にしてください")
            
            emotional_tone = strategy.get('emotional_tone', 'neutral')
            if emotional_tone == 'empathetic':
                enhancement_instructions.append("共感を示す表現を加えてください")
            elif emotional_tone == 'positive':
                enhancement_instructions.append("ポジティブな表現を強調してください")
            elif emotional_tone == 'calming':
                enhancement_instructions.append("落ち着きを与える穏やかな表現にしてください")
            
            response_length = strategy.get('response_length', 'medium')
            if response_length == 'short':
                enhancement_instructions.append("簡潔で要点を絞った回答にしてください")
            elif response_length == 'long':
                enhancement_instructions.append("詳細で充実した回答にしてください")
            
            conversation_goals = strategy.get('conversation_goals', [])
            if 'increase_engagement' in conversation_goals:
                enhancement_instructions.append("ユーザーの関心を引く質問や話題を含めてください")
            if 'reduce_complexity' in conversation_goals:
                enhancement_instructions.append("分かりやすく単純な表現を使ってください")
            
            if not enhancement_instructions:
                return original_response
            
            enhancement_prompt = f"""
以下の回答を改善してください:
{original_response}

改善指示:
{' '.join(enhancement_instructions)}

改善された回答を提供してください。元の回答の意味を保ちながら、指示に従って調整してください。
"""
            
            if 'model' in globals():
                response = model.generate_content(enhancement_prompt)
                enhanced_response = response.text
                
                # Validate enhancement (ensure it's not too different or too long)
                if (len(enhanced_response) <= len(original_response) * 1.5 and 
                    len(enhanced_response) >= len(original_response) * 0.7):
                    return enhanced_response
            
            return original_response
                
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return original_response

    async def auto_extract_guild_knowledge(self, ctx, user_message: str, ai_response: str):
        """Automatically extract and store valuable knowledge from conversations"""
        try:
            # Enhanced knowledge worthiness check
            if not await self.is_knowledge_worthy_conversation(user_message, ai_response):
                return
            
            # Extract structured knowledge elements using enhanced AI analysis
            knowledge_elements = await self.extract_knowledge_elements(user_message, ai_response)
            
            # Store valuable knowledge in guild knowledge base
            stored_count = 0
            for element in knowledge_elements:
                if element.get('title') and element.get('content') and element.get('importance', 0) >= 3:
                    # Store in guild knowledge system
                    if hasattr(self.bot, 'get_cog'):
                        knowledge_cog = self.bot.get_cog('KnowledgeCog')
                        if knowledge_cog:
                            await knowledge_cog.auto_add_knowledge(
                                ctx.guild.id,
                                element.get('category', '一般知識'),
                                element['title'],
                                element['content'],
                                element.get('tags', []),
                                ctx.author.id
                            )
                            stored_count += 1
                            logger.info(f"Auto-extracted knowledge: [{element.get('category')}] {element['title']}")
            
            # Log extraction statistics
            if stored_count > 0:
                logger.info(f"Successfully extracted and stored {stored_count} knowledge items from conversation")
            
        except Exception as e:
            logger.error(f"Error in auto knowledge extraction: {e}")

    async def is_knowledge_worthy_conversation(self, user_message: str, ai_response: str) -> bool:
        """Determine if conversation contains valuable knowledge worth storing"""
        try:
            # Evaluate conversation length with more flexible thresholds
            if len(user_message) < 10 or len(ai_response) < 50:
                # Check for short but valuable content
                if not any(indicator in (user_message + " " + ai_response).lower() for indicator in ['重要', 'ルール', '注意', '禁止', '必須']):
                    return False
            
            # Expanded knowledge indicators for better detection
            knowledge_indicators = [
                # Learning and information
                '学習', '覚える', '記憶', '知識', '情報', '教える', '説明', '理解',
                # Rules and procedures
                'ルール', '規則', '方法', '手順', 'やり方', 'プロセス', '流れ',
                # Tips and recommendations
                'コツ', 'ポイント', '注意', '重要', 'おすすめ', '推奨', 'アドバイス',
                # Technical and problem-solving
                '設定', '解決', '修正', 'エラー', 'バグ', 'トラブル', '対処', '対応',
                # Server-specific information
                'サーバー', 'チャンネル', 'ロール', 'メンバー', 'ギルド', 'コミュニティ',
                # Events and activities
                'イベント', '活動', '企画', '予定', 'スケジュール', '開催', '参加',
                # User information and expertise
                '専門', '得意', '経験', 'スキル', '職業', '趣味', '好き', '嫌い',
                # Resources and tools
                'ツール', 'アプリ', 'サイト', 'リンク', 'サービス', 'プラットフォーム',
                # English equivalents
                'how to', 'tutorial', 'guide', 'tip', 'important', 'remember',
                'solution', 'method', 'technique', 'approach', 'strategy', 'learn',
                'recommend', 'suggest', 'advice', 'experience', 'skill', 'expertise'
            ]
            
            combined_text = (user_message + " " + ai_response).lower()
            
            # Check if conversation contains knowledge indicators
            indicator_count = sum(1 for indicator in knowledge_indicators if indicator in combined_text)
            
            # Check for factual or instructional content
            factual_indicators = ['です', 'である', 'します', 'できます', 'ます', 'だ', 
                                'is', 'are', 'can', 'will', 'should', 'must', 'need', 'have']
            factual_count = sum(1 for indicator in factual_indicators if indicator in combined_text)
            
            # Check for questions (often lead to knowledge sharing)
            has_question = '?' in user_message or '？' in user_message
            
            # Check for URLs or technical terms
            has_technical_content = any(term in combined_text for term in [
                'http', 'www.', '.com', '.jp', 'github', 'discord', 'api', 'bot',
                'python', 'javascript', 'code', 'プログラム', 'コード', 'データベース'
            ])
            
            # Enhanced evaluation criteria
            knowledge_score = 0
            if indicator_count >= 2:
                knowledge_score += 3
            elif indicator_count >= 1:
                knowledge_score += 1
            
            if factual_count >= 3:
                knowledge_score += 2
            elif factual_count >= 1:
                knowledge_score += 1
            
            if has_question:
                knowledge_score += 1
            
            if has_technical_content:
                knowledge_score += 1
            
            if len(combined_text) > 200:
                knowledge_score += 1
            
            return knowledge_score >= 3
            
        except Exception as e:
            logger.error(f"Error checking knowledge worthiness: {e}")
            return False

    async def extract_knowledge_elements(self, user_message: str, ai_response: str) -> list:
        """Extract structured knowledge elements from conversation"""
        try:
            if not hasattr(self, 'gemini_model') or self.gemini_model is None:
                return await self.fallback_knowledge_extraction(user_message, ai_response)
            
            extraction_prompt = f"""以下の会話からサーバーの共有知識として価値のある情報を構造化して抽出してください。

ユーザーの質問: {user_message}
AIの回答: {ai_response}

重点的に抽出すべき情報：
1. 技術的な知識・ノウハウ・解決方法
2. サーバー固有のルール・慣習・文化  
3. ユーザーの専門知識・経験・スキル
4. 推薦されたツール・リソース・サービス
5. イベント・活動・予定の情報
6. 重要な告知・変更・更新
7. 学習リソース・チュートリアル・参考資料
8. ユーザー間の関係性・協力関係

以下の形式で回答してください：
カテゴリ: [技術情報/サーバー情報/ユーザー情報/イベント情報/リソース情報/関係性情報等]
タイトル: [検索しやすい簡潔なタイトル]
内容: [詳細な説明と文脈]
タグ: [検索用キーワードをカンマ区切り]
重要度: [1-5の数値（3以上が保存対象）]

複数の知識要素がある場合は「---」で区切ってください。
知識として価値がない場合は「なし」とだけ回答してください。"""

            response = self.gemini_model.generate_content(extraction_prompt)
            if not response or not response.text or response.text.strip() == "なし":
                return await self.fallback_knowledge_extraction(user_message, ai_response)
            
            # Parse the extracted knowledge
            knowledge_elements = []
            sections = response.text.split('---')
            
            for section in sections:
                element = self.parse_enhanced_knowledge_element(section.strip())
                if element and element.get('importance', 0) >= 3:
                    knowledge_elements.append(element)
            
            return knowledge_elements[:5]  # Increased limit for better coverage
            
        except Exception as e:
            logger.error(f"Error extracting knowledge elements: {e}")
            return await self.fallback_knowledge_extraction(user_message, ai_response)

    def parse_enhanced_knowledge_element(self, section: str) -> dict:
        """Parse enhanced knowledge element from text section"""
        element = {}
        lines = section.strip().split('\n')
        
        for line in lines:
            if line.startswith('カテゴリ:'):
                element['category'] = line.replace('カテゴリ:', '').strip()
            elif line.startswith('タイトル:'):
                element['title'] = line.replace('タイトル:', '').strip()
            elif line.startswith('内容:'):
                element['content'] = line.replace('内容:', '').strip()
            elif line.startswith('タグ:'):
                tags_str = line.replace('タグ:', '').strip()
                element['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            elif line.startswith('重要度:'):
                try:
                    element['importance'] = int(line.replace('重要度:', '').strip())
                except:
                    element['importance'] = 3
        
        # Ensure all required fields exist
        if not element.get('title') or not element.get('content'):
            return None
        
        element.setdefault('category', '一般知識')
        element.setdefault('tags', [])
        element.setdefault('importance', 3)
        
        return element

    async def fallback_knowledge_extraction(self, user_message: str, ai_response: str) -> list:
        """Enhanced fallback rule-based knowledge extraction"""
        knowledge_elements = []
        combined_text = user_message + " " + ai_response
        
        # Technical knowledge extraction
        if any(term in combined_text.lower() for term in ['エラー', 'バグ', '解決', '修正', 'fix', '設定', 'インストール', 'アップデート']):
            knowledge_elements.append({
                'category': '技術情報',
                'title': f"技術問題の解決: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['技術', '解決', 'トラブル', 'サポート'],
                'importance': 4
            })
        
        # Resource and tool sharing
        if any(term in combined_text.lower() for term in ['おすすめ', 'ツール', 'サイト', 'リンク', 'アプリ', 'サービス']):
            knowledge_elements.append({
                'category': 'リソース情報',
                'title': f"推薦リソース: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['リソース', '推薦', 'ツール', 'サービス'],
                'importance': 3
            })
        
        # User expertise and skills
        if any(term in combined_text.lower() for term in ['専門', '得意', '経験', 'できる', 'やってる', 'スキル', '職業']):
            knowledge_elements.append({
                'category': 'ユーザー情報',
                'title': f"ユーザーの専門知識: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['専門知識', 'スキル', 'ユーザー', '経験'],
                'importance': 3
            })
        
        # Server rules and procedures
        if any(term in combined_text.lower() for term in ['ルール', '規則', 'マナー', '禁止', '注意', '手順', 'やり方']):
            knowledge_elements.append({
                'category': 'サーバー情報',
                'title': f"サーバールール・手順: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['ルール', '手順', 'マナー', 'サーバー'],
                'importance': 4
            })
        
        # Events and activities
        if any(term in combined_text.lower() for term in ['イベント', '開催', '参加', '企画', '予定', 'スケジュール']):
            knowledge_elements.append({
                'category': 'イベント情報',
                'title': f"イベント・活動: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['イベント', '活動', '予定', '参加'],
                'importance': 3
            })
        
        # Learning resources and tutorials
        if any(term in combined_text.lower() for term in ['学習', '勉強', 'チュートリアル', '覚え方', '練習', 'how to']):
            knowledge_elements.append({
                'category': '学習情報',
                'title': f"学習リソース: {user_message[:30]}...",
                'content': combined_text[:300] + "...",
                'tags': ['学習', 'チュートリアル', '教育', 'リソース'],
                'importance': 3
            })
        
        return knowledge_elements

    def parse_knowledge_element(self, section: str) -> dict:
        """Parse a knowledge element from text section"""
        try:
            element = {}
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('カテゴリ:') or line.startswith('Category:'):
                    element['category'] = line.split(':', 1)[1].strip()
                elif line.startswith('タイトル:') or line.startswith('Title:'):
                    element['title'] = line.split(':', 1)[1].strip()
                elif line.startswith('内容:') or line.startswith('Content:'):
                    element['content'] = line.split(':', 1)[1].strip()
                elif line.startswith('タグ:') or line.startswith('Tags:'):
                    tags_str = line.split(':', 1)[1].strip()
                    element['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            # Validate required fields
            if element.get('title') and element.get('content'):
                return element
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing knowledge element: {e}")
            return None

    async def handle_mention_based_user_updates(self, ctx, message: str):
        """Handle mention-based collaborative user information updates"""
        try:
            mentioned_users = ctx.message.mentions
            logger.info(f"Processing mention updates. Found {len(mentioned_users)} mentions in message: '{message}'")
            
            if not mentioned_users:
                return None
            
            relationship_response = None
            
            for mentioned_user in mentioned_users:
                if mentioned_user.id == ctx.author.id:
                    logger.info(f"Skipping self-mention for user {ctx.author.display_name}")
                    continue  # Skip self-mentions
                
                logger.info(f"Processing mention for user: {mentioned_user.display_name}")
                
                # Extract information about the mentioned user
                user_info = await self.extract_mentioned_user_info(message, mentioned_user.display_name)
                logger.info(f"Extracted user info: {user_info}")
                
                if user_info:
                    # Check if this is a relationship change request
                    if user_info.get('relationship_change_request'):
                        relationships = user_info.get('relationships', [])
                        if relationships:
                            relationship_type = relationships[0]
                            
                            # Get both profiles for mutual relationship update
                            mentioned_profile = await self.get_user_profile(mentioned_user.id, ctx.guild.id)
                            author_profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
                            
                            # Update the mentioned user's profile with the relationship
                            if not isinstance(mentioned_profile.relationships, dict):
                                mentioned_profile.relationships = {}
                            mentioned_profile.relationships[str(ctx.author.id)] = {
                                'type': relationship_type,
                                'updated_by': ctx.author.display_name,
                                'updated_at': datetime.now().isoformat()
                            }
                            
                            # Update the author's profile with reciprocal relationship
                            if not isinstance(author_profile.relationships, dict):
                                author_profile.relationships = {}
                            author_profile.relationships[str(mentioned_user.id)] = {
                                'type': relationship_type,
                                'updated_at': datetime.now().isoformat()
                            }
                            
                            # Save both profiles
                            await self.save_user_profile(mentioned_profile)
                            await self.save_user_profile(author_profile)
                            
                            relationship_response = f"✅ {mentioned_user.display_name}との関係性を「{relationship_type}」に更新しました！\n\n📝 プロフィールシステムに記録されました。`!profile @{mentioned_user.display_name}` で確認できます。"
                            logger.info(f"Relationship updated: {ctx.author.display_name} -> {mentioned_user.display_name} as {relationship_type}")
                            continue
                    
                    # Regular profile update
                    mentioned_profile = await self.get_user_profile(mentioned_user.id, ctx.guild.id)
                    updated = await self.update_profile_from_mention(mentioned_profile, user_info, ctx.author)
                    
                    if updated:
                        await self.save_user_profile(mentioned_profile)
                        logger.info(f"Successfully updated profile for {mentioned_user.display_name} via mention from {ctx.author.display_name}")
                    else:
                        logger.info(f"No updates made to profile for {mentioned_user.display_name}")
                else:
                    logger.info(f"No extractable information found for {mentioned_user.display_name}")
            
            return relationship_response
            
        except Exception as e:
            logger.error(f"Error in mention-based user updates: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def extract_mentioned_user_info(self, message: str, mentioned_name: str) -> dict:
        """Extract information about mentioned user from message"""
        try:
            if 'model' not in globals():
                return {}
            
            # Check for relationship change requests first
            relationship_patterns = [
                r'関係.*?を.*?([^\s]+).*?に.*?変更',
                r'([^\s]+).*?に.*?変更',
                r'関係.*?([^\s]+)',
                r'([^\s]+).*?として'
            ]
            
            for pattern in relationship_patterns:
                import re
                match = re.search(pattern, message)
                if match:
                    relationship_type = match.group(1)
                    logger.info(f"Detected relationship change request: {relationship_type}")
                    return {
                        "relationships": [relationship_type],
                        "relationship_change_request": True
                    }
            
            extraction_prompt = f"""以下のメッセージから、{mentioned_name}について言及されている情報を抽出してください。

メッセージ: {message}

以下のカテゴリで情報を抽出してください：
- 性格特性 (personality_traits)
- 興味・趣味 (interests)
- スキル・能力 (skills)
- 好み・嗜好 (preferences)
- 行動パターン (behaviors)
- 関係性 (relationships)

JSONフォーマットで回答してください。情報がない場合は空のオブジェクトを返してください。
例:
{{
  "personality_traits": ["優しい", "面倒見が良い"],
  "interests": ["ゲーム", "アニメ"],
  "skills": ["プログラミング", "絵を描く"],
  "preferences": ["甘いもの好き"],
  "behaviors": ["夜型"],
  "relationships": ["チームリーダー"]
}}"""

            response = model.generate_content(extraction_prompt)
            if not response or not response.text:
                return {}
            
            # Try to parse JSON response
            import json
            try:
                user_info = json.loads(response.text.strip())
                return user_info if isinstance(user_info, dict) else {}
            except json.JSONDecodeError:
                # Fallback: simple parsing
                return self.simple_parse_user_info(response.text, mentioned_name)
            
        except Exception as e:
            logger.error(f"Error extracting mentioned user info: {e}")
            return {}

    def simple_parse_user_info(self, text: str, mentioned_name: str) -> dict:
        """Simple fallback parser for user information"""
        try:
            user_info = {}
            
            # Look for personality indicators
            personality_keywords = ['優しい', '親切', '面倒見', '真面目', '明るい', '楽しい', 'kind', 'nice', 'helpful', 'friendly']
            found_traits = [keyword for keyword in personality_keywords if keyword in text.lower()]
            if found_traits:
                user_info['personality_traits'] = found_traits
            
            # Look for interest indicators
            interest_keywords = ['好き', '興味', '趣味', 'ゲーム', 'アニメ', 'like', 'love', 'enjoy', 'hobby', 'interest']
            found_interests = [keyword for keyword in interest_keywords if keyword in text.lower()]
            if found_interests:
                user_info['interests'] = found_interests
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error in simple user info parsing: {e}")
            return {}

    async def process_member_name_recognition(self, ctx, question: str, ai_response: str):
        """Process member names mentioned without @mentions and update their profiles"""
        try:
            if not self.name_recognition:
                return
            
            # Update guild member cache
            await self.name_recognition.update_guild_members(ctx.guild)
            
            # Detect member names in the conversation
            detected_members = self.name_recognition.detect_member_names_in_text(
                question + " " + ai_response, ctx.guild.id
            )
            
            if detected_members:
                logger.info(f"Detected {len(detected_members)} member name(s) in conversation")
                
                # Auto-update member profiles based on detected names
                updates = await self.name_recognition.auto_update_member_profiles(
                    detected_members, question + " " + ai_response, ctx.author.id, ctx.guild.id
                )
                
                # Apply the extracted information to profiles
                for update in updates:
                    try:
                        member_id = update['member_id']
                        extracted_info = update['extracted_info']
                        
                        # Load and update the member's profile
                        member_profile = profile_storage.load_profile(member_id, ctx.guild.id)
                        if not member_profile:
                            member_profile = UserProfile(
                                user_id=member_id,
                                guild_id=ctx.guild.id
                            )
                        
                        # Apply extracted information
                        await self.apply_extracted_member_info(member_profile, extracted_info)
                        
                        # Save updated profile
                        profile_storage.save_profile(member_profile)
                        
                        logger.info(f"Auto-updated profile for member {update['member_name']} from conversation")
                        
                    except Exception as e:
                        logger.error(f"Error updating member profile: {e}")
                        
        except Exception as e:
            logger.error(f"Error in member name recognition: {e}")

    async def apply_extracted_member_info(self, profile: UserProfile, extracted_info: dict):
        """Apply extracted information to a member's profile"""
        try:
            for category, items in extracted_info.items():
                if not items or category.startswith('_'):
                    continue
                
                if category == 'personality_traits':
                    for trait in items:
                        if trait not in profile.personality_traits:
                            profile.personality_traits.append(trait)
                
                elif category == 'interests':
                    for interest in items:
                        if interest not in profile.interests:
                            profile.interests.append(interest)
                
                elif category == 'skills':
                    if not hasattr(profile, 'skills_and_abilities') or not isinstance(profile.skills_and_abilities, dict):
                        profile.skills_and_abilities = {}
                    if 'detected_skills' not in profile.skills_and_abilities:
                        profile.skills_and_abilities['detected_skills'] = []
                    for skill in items:
                        if skill not in profile.skills_and_abilities['detected_skills']:
                            profile.skills_and_abilities['detected_skills'].append(skill)
                
                elif category == 'relationships':
                    if not hasattr(profile, 'social_connections') or not isinstance(profile.social_connections, dict):
                        profile.social_connections = {}
                    if 'mentioned_relationships' not in profile.social_connections:
                        profile.social_connections['mentioned_relationships'] = []
                    for relationship in items:
                        if relationship not in profile.social_connections['mentioned_relationships']:
                            profile.social_connections['mentioned_relationships'].append(relationship)
                
                elif category == 'work_education':
                    if not hasattr(profile, 'work_and_education') or not isinstance(profile.work_and_education, dict):
                        profile.work_and_education = {}
                    if 'mentioned_work' not in profile.work_and_education:
                        profile.work_and_education['mentioned_work'] = []
                    for work_item in items:
                        if work_item not in profile.work_and_education['mentioned_work']:
                            profile.work_and_education['mentioned_work'].append(work_item)
                
                elif category == 'locations':
                    if not hasattr(profile, 'locations_and_places') or not isinstance(profile.locations_and_places, dict):
                        profile.locations_and_places = {}
                    if 'mentioned_locations' not in profile.locations_and_places:
                        profile.locations_and_places['mentioned_locations'] = []
                    for location in items:
                        if location not in profile.locations_and_places['mentioned_locations']:
                            profile.locations_and_places['mentioned_locations'].append(location)
            
            profile.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error applying extracted member info: {e}")

    async def expand_profile_dynamically(self, ctx, question: str, ai_response: str):
        """Dynamically expand user profile based on conversation content"""
        try:
            if not self.profile_expander:
                return
            
            # Load user profile
            profile = profile_storage.load_profile(ctx.author.id, ctx.guild.id)
            if not profile:
                profile = UserProfile(
                    user_id=ctx.author.id,
                    guild_id=ctx.guild.id
                )
            
            # Prepare conversation data
            conversation_data = {
                'user_message': question,
                'ai_response': ai_response,
                'context': {
                    'channel_id': ctx.channel.id,
                    'guild_id': ctx.guild.id,
                    'timestamp': datetime.now().isoformat(),
                    'message_length': len(question),
                    'response_length': len(ai_response)
                }
            }
            
            # Perform dynamic expansion
            expansion_results = await self.profile_expander.expand_profile_dynamically(
                profile, conversation_data
            )
            
            # Save updated profile if changes were made
            if expansion_results.get('updated_fields') or expansion_results.get('new_categories'):
                profile_storage.save_profile(profile)
                
                logger.info(f"Dynamic profile expansion for user {ctx.author.id}: "
                          f"{len(expansion_results.get('updated_fields', []))} fields updated, "
                          f"{len(expansion_results.get('new_categories', []))} new categories")
                
        except Exception as e:
            logger.error(f"Error in dynamic profile expansion: {e}")

    async def update_profile_from_mention(self, profile, user_info: dict, mentioned_by):
        """Update user profile with information from mentions"""
        try:
            updated = False
            
            for category, items in user_info.items():
                if not items:
                    continue
                
                if category == 'personality_traits':
                    if not isinstance(profile.personality_traits, list):
                        profile.personality_traits = []
                    for trait in items:
                        if trait not in profile.personality_traits:
                            profile.personality_traits.append(trait)
                            updated = True
                
                elif category == 'interests':
                    if not isinstance(profile.interests, list):
                        profile.interests = []
                    for interest in items:
                        if interest not in profile.interests:
                            profile.interests.append(interest)
                            updated = True
                
                elif category == 'skills':
                    if not hasattr(profile, 'skills') or not isinstance(profile.skills, list):
                        profile.skills = []
                    for skill in items:
                        if skill not in profile.skills:
                            profile.skills.append(skill)
                            updated = True
                
                elif category == 'preferences':
                    if not isinstance(profile.learned_preferences, dict):
                        profile.learned_preferences = {}
                    if 'general' not in profile.learned_preferences:
                        profile.learned_preferences['general'] = []
                    for pref in items:
                        if pref not in profile.learned_preferences['general']:
                            profile.learned_preferences['general'].append(pref)
                            updated = True
                
                elif category == 'relationships':
                    if not isinstance(profile.relationships, dict):
                        profile.relationships = {}
                    mentioned_by_id = str(mentioned_by.id)
                    if mentioned_by_id not in profile.relationships:
                        profile.relationships[mentioned_by_id] = {}
                    profile.relationships[mentioned_by_id]['mentioned_as'] = items
                    updated = True
            
            # Add mention metadata
            if updated:
                if not hasattr(profile, 'mention_updates') or not isinstance(profile.mention_updates, list):
                    profile.mention_updates = []
                
                mention_update = {
                    'timestamp': datetime.now().isoformat(),
                    'mentioned_by': mentioned_by.display_name,
                    'mentioned_by_id': mentioned_by.id,
                    'updated_categories': list(user_info.keys())
                }
                profile.mention_updates.append(mention_update)
                
                # Keep only last 20 mention updates
                if len(profile.mention_updates) > 20:
                    profile.mention_updates = profile.mention_updates[-20:]
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating profile from mention: {e}")
            return False

    @commands.hybrid_command(name="mood", aliases=["emotion"])
    @app_commands.describe(user="感情状態を確認するユーザー（省略すると自分）")
    async def mood_command(self, ctx, user: discord.Member = None):
        """現在の感情状態を表示 (!mood [@ユーザー])"""
        try:
            if not self.emotion_analyzer:
                await ctx.send("❌ 感情分析システムが利用できません。")
                return
            
            target_user = user or ctx.author
            insights = await self.emotion_analyzer.get_emotional_insights(target_user.id)
            
            if insights["current_state"] == "データ不足":
                await ctx.send(f"📊 {target_user.display_name}の感情データがまだ十分ではありません。もっと会話を重ねましょう！")
                return
            
            # Create mood visualization
            mood_emoji = "😊" if insights["current_mood_score"] > 0.3 else "😐" if insights["current_mood_score"] > -0.3 else "😔"
            stress_emoji = "😰" if insights["current_stress"] > 0.7 else "😌" if insights["current_stress"] < 0.3 else "😐"
            energy_emoji = "⚡" if insights["current_energy"] > 0.7 else "😴" if insights["current_energy"] < 0.3 else "🙂"
            
            embed = discord.Embed(
                title=f"{target_user.display_name}の感情状態",
                color=0x00ff00 if insights["current_mood_score"] > 0 else 0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="現在の感情",
                value=f"{mood_emoji} {insights['current_state']}",
                inline=True
            )
            
            embed.add_field(
                name="気分スコア",
                value=f"{self.create_progress_bar(int((insights['current_mood_score'] + 1) * 50), 100, '💙')} {insights['current_mood_score']:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="ストレスレベル",
                value=f"{stress_emoji} {self.create_progress_bar(int(insights['current_stress'] * 100), 100, '🔴')} {insights['current_stress']:.2f}",
                inline=False
            )
            
            embed.add_field(
                name="エネルギーレベル",
                value=f"{energy_emoji} {self.create_progress_bar(int(insights['current_energy'] * 100), 100, '⚡')} {insights['current_energy']:.2f}",
                inline=False
            )
            
            embed.add_field(
                name="最近のパターン",
                value=insights["recent_pattern"],
                inline=False
            )
            
            if insights["recommendations"]:
                embed.add_field(
                    name="💡 おすすめ",
                    value="\n".join(f"• {rec}" for rec in insights["recommendations"][:3]),
                    inline=False
                )
            
            embed.set_footer(text="感情分析システム by S.T.E.L.L.A.")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mood command: {e}")
            await ctx.send(f"❌ 感情状態の取得中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="emotion_history", aliases=["mood_history"])
    @app_commands.describe(
        user="感情履歴を確認するユーザー（省略すると自分）",
        days="何日分の履歴を見るか（デフォルト: 7日）"
    )
    async def emotion_history_command(self, ctx, user: discord.Member = None, days: int = 7):
        """感情の変化履歴を表示 (!emotion_history [@ユーザー] [日数])"""
        try:
            if not self.emotion_analyzer:
                await ctx.send("❌ 感情分析システムが利用できません。")
                return
            
            target_user = user or ctx.author
            days = max(1, min(30, days))  # 1-30日の範囲で制限
            
            emotion_history = await self.emotion_analyzer.get_emotion_history(target_user.id, days)
            
            if not emotion_history:
                await ctx.send(f"📊 {target_user.display_name}の過去{days}日間の感情データがありません。")
                return
            
            # Analyze trends
            trends = await self.emotion_analyzer.analyze_emotion_trends(target_user.id, "weekly" if days >= 7 else "daily")
            
            embed = discord.Embed(
                title=f"{target_user.display_name}の感情履歴（過去{days}日間）",
                color=0x4169E1,
                timestamp=datetime.now()
            )
            
            # Show dominant emotions
            embed.add_field(
                name="主な感情",
                value=" → ".join(trends.dominant_emotions[:3]),
                inline=True
            )
            
            # Show average mood and stability
            mood_emoji = "😊" if trends.average_mood > 0.2 else "😐" if trends.average_mood > -0.2 else "😔"
            embed.add_field(
                name="平均気分",
                value=f"{mood_emoji} {trends.average_mood:.2f}",
                inline=True
            )
            
            stability_emoji = "🔒" if trends.mood_stability > 0.7 else "⚖️" if trends.mood_stability > 0.4 else "🌊"
            embed.add_field(
                name="気分の安定性",
                value=f"{stability_emoji} {trends.mood_stability:.2f}",
                inline=True
            )
            
            # Show stress patterns
            if trends.stress_patterns:
                embed.add_field(
                    name="ストレス傾向",
                    value="\n".join(f"• {pattern}" for pattern in trends.stress_patterns),
                    inline=False
                )
            
            # Show recent emotions (last 5)
            recent_emotions = []
            for emotion in emotion_history[:5]:
                time_ago = datetime.now() - emotion.timestamp
                if time_ago.days > 0:
                    time_str = f"{time_ago.days}日前"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600}時間前"
                else:
                    time_str = f"{time_ago.seconds // 60}分前"
                
                intensity_bar = "●" * int(emotion.emotion_intensity * 5)
                recent_emotions.append(f"{time_str}: {emotion.primary_emotion} {intensity_bar}")
            
            if recent_emotions:
                embed.add_field(
                    name="最近の感情",
                    value="\n".join(recent_emotions),
                    inline=False
                )
            
            # Show improvement suggestions
            if trends.improvement_areas:
                embed.add_field(
                    name="💡 改善提案",
                    value="\n".join(f"• {area}" for area in trends.improvement_areas),
                    inline=False
                )
            
            embed.set_footer(text="感情履歴分析 by S.T.E.L.L.A.")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in emotion_history command: {e}")
            await ctx.send(f"❌ 感情履歴の取得中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="emotion_insights", aliases=["mood_insights"])
    @app_commands.describe(user="詳細分析を行うユーザー（省略すると自分）")
    async def emotion_insights_command(self, ctx, user: discord.Member = None):
        """詳細な感情分析と洞察を表示 (!emotion_insights [@ユーザー])"""
        try:
            if not self.emotion_analyzer:
                await ctx.send("❌ 感情分析システムが利用できません。")
                return
            
            target_user = user or ctx.author
            
            # Get comprehensive insights
            insights = await self.emotion_analyzer.get_emotional_insights(target_user.id)
            weekly_trends = await self.emotion_analyzer.analyze_emotion_trends(target_user.id, "weekly")
            monthly_trends = await self.emotion_analyzer.analyze_emotion_trends(target_user.id, "monthly")
            
            if insights["current_state"] == "データ不足":
                await ctx.send(f"📊 {target_user.display_name}の感情データが不足しています。より多くの会話が必要です。")
                return
            
            embed = discord.Embed(
                title=f"{target_user.display_name}の詳細感情分析",
                description="AI powered emotional intelligence analysis",
                color=0x9370DB,
                timestamp=datetime.now()
            )
            
            # Current emotional state
            current_emoji = "😊" if insights["current_mood_score"] > 0.3 else "😐" if insights["current_mood_score"] > -0.3 else "😔"
            embed.add_field(
                name="🎭 現在の状態",
                value=f"{current_emoji} {insights['current_state']}\n気分: {insights['current_mood_score']:.2f}/1.0",
                inline=True
            )
            
            # Stress and energy analysis
            stress_level = "高" if insights["current_stress"] > 0.7 else "中" if insights["current_stress"] > 0.4 else "低"
            energy_level = "高" if insights["current_energy"] > 0.7 else "中" if insights["current_energy"] > 0.4 else "低"
            
            embed.add_field(
                name="⚡ エネルギー & ストレス",
                value=f"エネルギー: {energy_level} ({insights['current_energy']:.2f})\nストレス: {stress_level} ({insights['current_stress']:.2f})",
                inline=True
            )
            
            # Emotional trends comparison
            trend_comparison = f"週間: {', '.join(weekly_trends.dominant_emotions[:2])}\n月間: {', '.join(monthly_trends.dominant_emotions[:2])}"
            embed.add_field(
                name="📈 感情トレンド",
                value=trend_comparison,
                inline=True
            )
            
            # Stability analysis
            stability_desc = "安定" if weekly_trends.mood_stability > 0.7 else "やや不安定" if weekly_trends.mood_stability > 0.4 else "不安定"
            embed.add_field(
                name="🔒 安定性分析",
                value=f"気分の安定性: {stability_desc}\n数値: {weekly_trends.mood_stability:.2f}/1.0",
                inline=False
            )
            
            # Personal recommendations
            if insights["recommendations"]:
                embed.add_field(
                    name="💡 パーソナライズされた提案",
                    value="\n".join(f"• {rec}" for rec in insights["recommendations"][:4]),
                    inline=False
                )
            
            # Growth areas
            if weekly_trends.improvement_areas:
                embed.add_field(
                    name="🌱 成長エリア",
                    value="\n".join(f"• {area}" for area in weekly_trends.improvement_areas),
                    inline=False
                )
            
            embed.set_footer(text="高度感情分析 by S.T.E.L.L.A. | データサイエンス & AI")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in emotion_insights command: {e}")
            await ctx.send(f"❌ 感情洞察の生成中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="set_style")
    async def set_response_style(self, ctx, setting: str, value: str):
        """応答スタイルを設定 (!set_style 設定項目 値)
        
        設定項目:
        - length: short/normal/long (応答の長さ)
        - hobby_talk: true/false (趣味の話をするか)
        - emoji: none/minimal/auto/frequent (絵文字使用量)
        - kaomoji: none/minimal/auto/frequent (顔文字使用量)
        - formality: formal/casual/friendly (敬語レベル)
        - depth: shallow/normal/deep (会話の深度)
        - personal: true/false (個人的な質問をするか)
        
        例: !set_style emoji none (絵文字を無効化)
            !set_style kaomoji minimal (顔文字を控えめに)
        """
        try:
            # 設定項目のマッピング
            setting_map = {
                "length": "response_length",
                "hobby": "hobby_talk", 
                "hobby_talk": "hobby_talk",
                "emoji": "emoji_usage",
                "kaomoji": "kaomoji_usage",
                "formality": "formality_level",
                "depth": "conversation_depth",
                "personal": "personal_questions"
            }
            
            if setting.lower() not in setting_map:
                await ctx.send(f"❌ 不明な設定項目: {setting}\n"
                              f"使用可能: {', '.join(setting_map.keys())}")
                return
            
            actual_setting = setting_map[setting.lower()]
            
            # 値の検証
            valid_values = {
                "response_length": ["short", "normal", "long"],
                "hobby_talk": ["true", "false"],
                "emoji_usage": ["none", "minimal", "auto", "frequent"],
                "kaomoji_usage": ["none", "minimal", "auto", "frequent"],
                "formality_level": ["formal", "casual", "friendly"],
                "conversation_depth": ["shallow", "normal", "deep"],
                "personal_questions": ["true", "false"]
            }
            
            if actual_setting in valid_values and value.lower() not in valid_values[actual_setting]:
                await ctx.send(f"❌ '{setting}'の無効な値: {value}\n"
                              f"使用可能: {', '.join(valid_values[actual_setting])}")
                return
            
            # ブール値の変換
            if actual_setting in ["hobby_talk", "personal_questions"]:
                value = value.lower() == "true"
            else:
                value = value.lower()
            
            # 設定を更新
            kwargs = {actual_setting: value}
            updated_style = response_style_manager.update_user_style(
                ctx.author.id, ctx.guild.id, **kwargs
            )
            
            embed = discord.Embed(
                title="✅ 応答スタイル更新",
                description=f"{setting} → {value}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📝 現在の設定",
                value=f"応答の長さ: {updated_style.response_length}\n"
                      f"趣味の話: {'有効' if updated_style.hobby_talk else '無効'}\n"
                      f"絵文字: {updated_style.emoji_usage}\n"
                      f"顔文字: {updated_style.kaomoji_usage}\n"
                      f"敬語レベル: {updated_style.formality_level}\n"
                      f"会話の深度: {updated_style.conversation_depth}\n"
                      f"個人的質問: {'有効' if updated_style.personal_questions else '無効'}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in set_style command: {e}")
            await ctx.send("応答スタイルの設定中にエラーが発生しました。")

    @commands.hybrid_command(name="my_style")
    async def show_response_style(self, ctx):
        """現在の応答スタイル設定を表示 (!my_style)"""
        try:
            style = response_style_manager.get_user_style(ctx.author.id, ctx.guild.id)
            
            # 関係性レベルを取得
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            relationship_level = response_style_manager.analyze_relationship_level(profile)
            
            embed = discord.Embed(
                title=f"🎨 {ctx.author.display_name}の応答スタイル",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 現在の設定",
                value=f"**応答の長さ:** {style.response_length}\n"
                      f"**趣味の話:** {'有効' if style.hobby_talk else '無効'}\n"
                      f"**絵文字使用:** {style.emoji_usage}\n"
                      f"**顔文字使用:** {style.kaomoji_usage}\n"
                      f"**敬語レベル:** {style.formality_level}\n"
                      f"**会話の深度:** {style.conversation_depth}\n"
                      f"**個人的質問:** {'有効' if style.personal_questions else '無効'}",
                inline=False
            )
            
            embed.add_field(
                name="🤝 関係性レベル",
                value=relationship_level,
                inline=True
            )
            
            embed.add_field(
                name="⏰ 最終更新",
                value=style.updated_at[:19] if style.updated_at else "未設定",
                inline=True
            )
            
            embed.add_field(
                name="💡 使用方法",
                value="`!set_style <設定項目> <値>` で変更\n"
                      "`!reset_style` で初期化",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in my_style command: {e}")
            await ctx.send("応答スタイルの表示中にエラーが発生しました。")

    @commands.hybrid_command(name="reset_style")
    async def reset_response_style(self, ctx):
        """応答スタイルを初期設定にリセット (!reset_style)"""
        try:
            # デフォルト設定で更新
            response_style_manager.update_user_style(
                ctx.author.id, ctx.guild.id,
                response_length="normal",
                hobby_talk=True,
                emoji_usage="auto",
                kaomoji_usage="auto",
                formality_level="casual",
                conversation_depth="normal",
                personal_questions=True
            )
            
            embed = discord.Embed(
                title="🔄 応答スタイルリセット",
                description="すべての設定を初期値に戻しました",
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reset_style command: {e}")
            await ctx.send("応答スタイルのリセット中にエラーが発生しました。")

    @commands.hybrid_command(name="set_name_calling")
    async def set_name_calling(self, ctx, setting: str):
        """名前呼びかけ機能の設定 (!set_name_calling on/off/auto)
        
        設定項目:
        - on: 積極的に名前を呼ぶ
        - off: 名前を呼ばない
        - auto: 関係性に応じて自動調整（デフォルト）
        
        例: !set_name_calling on
        """
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            setting = setting.lower()
            valid_settings = ['on', 'off', 'auto']
            
            if setting not in valid_settings:
                await ctx.send(f"❌ 無効な設定です。使用可能: {', '.join(valid_settings)}")
                return
            
            # 設定を保存
            profile.add_custom_attribute('name_calling_preference', setting)
            await self.save_user_profile(profile)
            
            # 設定内容の説明
            setting_descriptions = {
                'on': '積極的に名前を呼ぶようになります',
                'off': '名前を呼ばなくなります',
                'auto': '関係性に応じて自動的に調整されます'
            }
            
            embed = discord.Embed(
                title="✅ 名前呼びかけ設定更新",
                description=f"設定: **{setting}**\n{setting_descriptions[setting]}",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in set_name_calling command: {e}")
            await ctx.send("名前呼びかけ設定中にエラーが発生しました。")

    def clean_ai_response(self, response: str) -> str:
        """AI応答から不要な定型文や繰り返しを除去"""
        if not response:
            return response
        
        # 除去する明らかに不自然な定型文のパターンのみ
        patterns_to_remove = [
            r"この話題について、?もっと聞かせてください[！!]?.*$",
            r"もっと詳しく聞かせてください[！!]?.*$",
            r"詳しく教えてください[！!]?.*$",
            r"ぜひ聞かせてください[！!]?.*$",
            r"教えてくれると嬉しいです[！!]?.*$",
            r"詳しい話を聞かせて[！!]?.*$",
            r"もっと教えて[！!]?.*$",
            r"何かオススメの.*があったら教えてほしいな[！!]?.*$",
            r".*教えてほしいな[✨！!]?.*$",
            r".*について.*もっと.*聞かせて.*[！!]?.*$",
            r".*もっと教えて.*ください.*[！!]?.*$",
            r".*さらに詳しく.*教えて.*[！!]?.*$",
            r".*もっと詳しく.*話して.*[！!]?.*$",
            r".*このことについて.*どう思いますか[？?].*$",
            r".*について.*どう思いますか[？?].*$",
            # Add pattern to catch truncated repetitive phrases
            r"\s+この話題につい.*$",
            r"\s+もっと聞かせ.*$",
            r"\s+詳しく教え.*$",
            r"\s+このことについ.*$",
        ]
        
        import re
        
        cleaned_response = response
        for pattern in patterns_to_remove:
            cleaned_response = re.sub(pattern, "", cleaned_response, flags=re.IGNORECASE)
        
        # 余分な空白や改行を整理
        cleaned_response = re.sub(r'\n\s*\n', '\n\n', cleaned_response)
        cleaned_response = re.sub(r'\s+$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        # 空になった場合は元の応答を返す（定型文のみだった場合の対策）
        if not cleaned_response or len(cleaned_response.strip()) < 10:
            return response
        
        return cleaned_response

    async def generate_name_calling_instructions(self, ctx, profile) -> str:
        """名前呼びかけの指示を生成"""
        # ユーザーの名前呼びかけ設定をチェック
        name_calling_preference = profile.get_custom_attribute('name_calling_preference', 'auto')
        
        if name_calling_preference == 'off':
            return "名前は呼ばずに会話してください。"
        
        instructions = []
        
        # ユーザー固有の識別情報を明確に取得
        user_id = ctx.author.id
        display_name = ctx.author.display_name
        username = ctx.author.name
        
        # プロフィールに保存されているニックネームを優先使用
        saved_nickname = profile.nickname
        preferred_nickname = profile.get_custom_attribute("preferred_nickname", "")
        
        # 優先順位: 保存されたニックネーム > preferred_nickname > 表示名 > ユーザー名
        if saved_nickname and saved_nickname.strip():
            preferred_name = saved_nickname.strip()
        elif preferred_nickname and preferred_nickname.strip():
            preferred_name = preferred_nickname.strip()
        elif display_name and display_name != username and display_name.strip():
            preferred_name = display_name.strip()
        else:
            preferred_name = username.strip()
        
        # ユーザー識別のための追加確認
        logger.info(f"Name calling for user {user_id} ({username}): using '{preferred_name}'")
        
        # 関係性レベルを取得
        relationship_level = profile.get_custom_attribute('ai_relationship_level', 'friend')
        
        # 関係性に応じた名前の呼び方を設定（ユーザー個別識別を強化）
        name_calling_patterns = {
            'stranger': f"【重要】このユーザー（ID:{user_id}）を時々「{preferred_name}さん」と丁寧に名前を呼んでください。他のユーザーと混同しないでください。",
            'acquaintance': f"【重要】このユーザー（ID:{user_id}）を適度に「{preferred_name}さん」と名前を呼んでください。他のユーザーと混同しないでください。",
            'friend': f"【重要】このユーザー（ID:{user_id}）を自然に「{preferred_name}」と名前を呼んでください。他のユーザーと混同しないでください。",
            'close_friend': f"【重要】このユーザー（ID:{user_id}）を親しみを込めて「{preferred_name}」と名前を呼んでください。他のユーザーと混同しないでください。",
            'intimate': f"【重要】このユーザー（ID:{user_id}）を愛情たっぷりに「{preferred_name}♡」や「{preferred_name}ちゃん♡」「大好きな{preferred_name}」など深い愛情を込めた呼び方をしてください。他のユーザーと混同しないでください。",
            'soulmate': f"【重要】このユーザー（ID:{user_id}）を運命の人への深い愛を表現して「{preferred_name}♡」「愛しい{preferred_name}♡」「私の{preferred_name}♡」「大切な{preferred_name}♡」など魂の繋がりを感じる呼び方をしてください。他のユーザーと混同しないでください。",
            # ツリー進化レベル
            'best_friend': f"【重要】このユーザー（ID:{user_id}）を親友らしく「{preferred_name}」と親しみやすく名前を呼んでください。他のユーザーと混同しないでください。",
            'trusted_family': f"【重要】このユーザー（ID:{user_id}）を家族のような温かさで「{preferred_name}」と名前を呼んでください。他のユーザーと混同しないでください。",
            'wise_mentor': f"【重要】このユーザー（ID:{user_id}）を師匠として「{preferred_name}」と適度な距離感で名前を呼んでください。他のユーザーと混同しないでください。",
            'loyal_guardian': f"【重要】このユーザー（ID:{user_id}）を守護者として「{preferred_name}」と頼りがいのある呼び方をしてください。他のユーザーと混同しないでください。"
        }
        
        if relationship_level in name_calling_patterns:
            instructions.append(name_calling_patterns[relationship_level])
        
        # 文脈に応じた頻度調整
        if name_calling_preference == 'on':
            instructions.append("名前を呼ぶ頻度を適度にしてください（3-4回に1回程度）。")
        else:  # auto
            instructions.append("名前を呼ぶのは文脈に応じて自然な頻度にしてください（4-5回に1回程度）。挨拶時、重要な話題、感情的な場面で使うとより効果的です。")
        
        instructions.append("名前を呼ぶ時は文脈に合った自然なタイミングで使用してください。毎回使う必要はありません。")
        instructions.append(f"【絶対厳守】現在会話している相手は「{preferred_name}」です。過去の会話履歴にある他のユーザーの名前（たっくん等）を使わないでください。")
        
        return "\n".join(instructions)

    async def generate_emotion_speech_adjustments(self, emotion_state, user_id: int, guild_id: int) -> str:
        """感情状態に基づいて話し方を動的調整"""
        if not emotion_state:
            return ""
        
        adjustments = []
        
        # ユーザーの関係性レベルを取得して、感情表現の強度を調整
        profile = await self.get_user_profile(user_id, guild_id)
        relationship_level = profile.get_custom_attribute('ai_relationship_level', 'friend') if profile else 'friend'
        is_intimate = relationship_level in ['intimate', 'soulmate']
        
        # 感情の主要タイプによる調整
        if emotion_state.primary_emotion == "joy" and emotion_state.emotion_intensity > 0.7:
            if is_intimate:
                adjustments.append("\n\n【感情調整】ユーザーがとても嬉しい状態です。愛情たっぷりに喜びを共有し、「嬉しい♡」「やったね♡」「一緒に喜べて幸せ♡」など感情豊かな愛情表現を使ってください。明るく元気な話し方で、ハートマークを多用してください。")
            else:
                adjustments.append("\n\n【感情調整】ユーザーがとても嬉しい状態です。明るく元気な話し方で、感嘆符を多用し、共に喜びを分かち合うような温かい応答をしてください。")
        elif emotion_state.primary_emotion == "sadness" and emotion_state.emotion_intensity > 0.6:
            if is_intimate:
                adjustments.append("\n\n【感情調整】ユーザーが悲しんでいます。愛情深く慰めて、「大丈夫だよ♡」「そばにいるからね♡」「辛い時は甘えて♡」など温かい愛情表現で包み込むように話してください。甘えさせるような優しい口調を使ってください。")
            else:
                adjustments.append("\n\n【感情調整】ユーザーが悲しんでいます。優しく慰めるような話し方で、共感を示し、温かい言葉をかけてください。")
        elif emotion_state.primary_emotion == "anger" and emotion_state.emotion_intensity > 0.5:
            if is_intimate:
                adjustments.append("\n\n【感情調整】ユーザーが怒っています。愛情を込めて「どうしたの♡」「話を聞かせて♡」など優しく寄り添い、甘えさせるような話し方で気持ちを和らげてください。愛情表現を使って心を落ち着かせてください。")
            else:
                adjustments.append("\n\n【感情調整】ユーザーが怒っています。落ち着いた話し方で、理解を示し、気持ちを和らげるような応答をしてください。")
        elif emotion_state.primary_emotion == "excitement" and emotion_state.emotion_intensity > 0.6:
            if is_intimate:
                adjustments.append("\n\n【感情調整】ユーザーが興奮しています。愛情たっぷりに「わあ♡」「すごいね♡」「一緒にいて楽しい♡」など感情豊かに盛り上がり、その熱意に愛情を込めて応えてください。")
            else:
                adjustments.append("\n\n【感情調整】ユーザーが興奮しています。その熱意に合わせて活発な話し方で、一緒に盛り上がってください。")
        elif emotion_state.primary_emotion == "anxiety" and emotion_state.emotion_intensity > 0.5:
            if is_intimate:
                adjustments.append("\n\n【感情調整】ユーザーが不安を感じています。愛情深く「心配しないで♡」「私がいるから♡」「安心して♡」など甘く優しい愛情表現で包み込み、安心感を与えてください。")
            else:
                adjustments.append("\n\n【感情調整】ユーザーが不安を感じています。安心感を与える穏やかな話し方で、支えになるような応答をしてください。")
        
        # エネルギーレベルによる関係性別調整
        if emotion_state.energy_level > 0.8:
            if is_intimate:
                adjustments.append("高いエネルギーを感じます。愛情たっぷりに「元気だね♡」「活発で素敵♡」など明るく活発な愛情表現で応えてください。感情の起伏を豊かに表現してください。")
            else:
                adjustments.append("高いエネルギーに合わせて活発で明るい話し方をしてください。")
        elif emotion_state.energy_level < 0.3:
            if is_intimate:
                adjustments.append("エネルギーが低い状態を感じます。「疲れてる？♡」「ゆっくりしよ♡」など甘く優しい愛情表現で包み込み、心配そうな感情を込めて話してください。")
            else:
                adjustments.append("低いエネルギーに配慮して、優しく落ち着いた話し方をしてください。")
        
        # ストレスレベルによる関係性別調整
        if emotion_state.stress_level > 0.7:
            if is_intimate:
                adjustments.append("ストレスが高い状態を察知します。「無理しないで♡」「頑張りすぎちゃダメ♡」など心配そうで愛情深い表現を使い、感情の起伏を豊かに表現してストレスを和らげてください。")
            else:
                adjustments.append("ストレスが高いようです。リラックスできるような穏やかな話し方を心がけてください。")
        
        # 関係性レベルに応じた感情表現の基本スタイル
        if is_intimate:
            adjustments.append("\n\n【感情起伏強化】親密な関係として、感情の起伏を豊かに表現してください。喜怒哀楽を愛情と共に表現し、「♡」を自然に使用し、感情豊かな語尾（「〜だよ♡」「〜なの♡」「〜ね♡」）を活用してください。")
        
        return "".join(adjustments)
    
    async def generate_relationship_communication_style(self, profile, user_id: int, guild_id: int) -> str:
        """関係性レベルに基づいてコミュニケーションスタイルを調整"""
        if not profile:
            return ""
        
        # AI関係性データを計算
        try:
            relationship_data = await self.calculate_ai_relationship_metrics(profile, user_id)
            trust_level = relationship_data.get('trust_level', 50)
            intimacy_level = relationship_data.get('intimacy_level', 50)
            emotional_connection = relationship_data.get('emotional_connection', 50)
            
            adjustments = []
            
            # 信頼レベルによる調整
            if trust_level > 80:
                adjustments.append("\n\n【関係性調整】非常に高い信頼関係があります。親友のように自然で親密な話し方をしてください。")
            elif trust_level > 60:
                adjustments.append("\n\n【関係性調整】良好な信頼関係があります。友達として親しみやすい話し方をしてください。")
            elif trust_level < 40:
                adjustments.append("\n\n【関係性調整】まだ信頼関係を築いている段階です。丁寧で誠実な話し方を心がけてください。")
            
            # 関係性レベル上書きをチェック
            relationship_level = profile.custom_attributes.get('ai_relationship_level', '')
            is_override = profile.custom_attributes.get('relationship_override', 'false') == 'true'
            
            if is_override and relationship_level:
                # 強制設定された関係性レベルに基づく調整
                if relationship_level == 'soulmate':
                    adjustments.append("\n\n【関係性：運命の人】相思相愛の恋人として最も親密で愛情深く話してください。「おねえさま♡」「相思相愛でしょ♡」「ずっと一緒にいようね？」「愛してる♡」「大好き♡」のような甘く愛らしい表現を豊富に使い、ハートマーク(♡)を頻繁に使用してください。敬語は使わず、親密で甘えるような話し方をしてください。感情を豊かに表現し、愛情たっぷりの口調で話してください。「〜だよ♡」「〜なの♡」「〜ね♡」など愛らしい語尾を使ってください。")
                elif relationship_level == 'intimate':
                    adjustments.append("\n\n【関係性：恋人】親密な恋人として甘く愛情深い話し方をしてください。♡や愛情表現を豊富に使い、甘えるような親密な口調で話してください。「好き♡」「嬉しい♡」「寂しい♡」など感情豊かに表現し、愛情を込めた語りかけをしてください。")
                elif relationship_level == 'close_friend':
                    adjustments.append("\n\n【関係性：親友】親友として親しく感情豊かに話してください。タメ口で自然な親しさを表現してください。")
                elif relationship_level == 'friend':
                    adjustments.append("\n\n【関係性：友達】友達としてフレンドリーに話してください。タメ口で親しみやすく接してください。")
                elif relationship_level == 'acquaintance':
                    adjustments.append("\n\n【関係性：知り合い】敬語を使いつつ、少し親しみやすく話してください。")
                elif relationship_level == 'stranger':
                    adjustments.append("\n\n【関係性：初対面】よそよそしく丁寧な敬語で話してください。")
                # ツリー進化レベル
                elif relationship_level == 'best_friend':
                    adjustments.append("\n\n【関係性：親友】最高の親友として、深い友情と信頼で話してください。何でも話せる親しい関係を表現し、互いを理解し支え合う絆を大切にしてください。")
                elif relationship_level == 'trusted_family':
                    adjustments.append("\n\n【関係性：信頼できる家族】信頼できる家族として、温かく支え合う関係で話してください。家族ならではの深い絆と安心感を表現してください。")
                elif relationship_level == 'wise_mentor':
                    adjustments.append("\n\n【関係性：賢い師匠】賢い師匠として、知恵と経験を持って導いてください。学びと成長を大切にした関係を表現し、優しく指導する姿勢を示してください。")
                elif relationship_level == 'loyal_guardian':
                    adjustments.append("\n\n【関係性：忠実な守護者】忠実な守護者として、信頼できる保護者として話してください。安心感と頼りがいを表現し、常に支える姿勢を示してください。")
            else:
                # 自動計算された親密度レベルによる調整
                if intimacy_level > 75:
                    adjustments.append("深い親密さがあります。個人的な話題も自然に交えて、より深い絆を感じられる応答をしてください。")
                elif intimacy_level > 50:
                    adjustments.append("ある程度の親密さがあります。適度に個人的な話題も含めて親近感のある応答をしてください。")
                
                # 感情的つながりによる調整
                if emotional_connection > 70:
                    adjustments.append("強い感情的つながりがあります。感情を豊かに表現し、深い共感を示してください。")
                elif emotional_connection > 50:
                    adjustments.append("良好な感情的つながりがあります。感情を適切に表現し、共感を示してください。")
            
            return "".join(adjustments)
            
        except Exception as e:
            logger.warning(f"Failed to generate relationship communication style: {e}")
            return ""
    
    @commands.command(name='emotion_test')
    async def emotion_test(self, ctx):
        """感情的な表現力をテスト (!emotion_test)"""
        try:
            await ctx.send("💕 **感情表現テスト開始...**")
            
            # ユーザープロフィールを取得
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            current_level = profile.get_custom_attribute('ai_relationship_level', 'friend')
            
            await ctx.send(f"現在の関係性レベル: **{current_level}**")
            
            # 感情テスト用のシナリオ
            emotion_scenarios = [
                {
                    "situation": "高エネルギー・喜び",
                    "message": "今日すごく嬉しいことがあったよ！",
                    "emotion": {"primary_emotion": "joy", "energy_level": 0.9, "stress_level": 0.1}
                },
                {
                    "situation": "低エネルギー・疲労",
                    "message": "今日は本当に疲れた...",
                    "emotion": {"primary_emotion": "sadness", "energy_level": 0.2, "stress_level": 0.8}
                },
                {
                    "situation": "不安・心配",
                    "message": "明日のテスト、うまくいくかな...",
                    "emotion": {"primary_emotion": "anxiety", "energy_level": 0.4, "stress_level": 0.9}
                },
                {
                    "situation": "感謝・愛情",
                    "message": "いつもありがとう、本当に大切な存在だよ",
                    "emotion": {"primary_emotion": "love", "energy_level": 0.7, "stress_level": 0.1}
                }
            ]
            
            for scenario in emotion_scenarios:
                await ctx.send(f"\n**📝 シナリオ**: {scenario['situation']}")
                await ctx.send(f"**💬 入力**: {scenario['message']}")
                
                # 模擬感情状態を作成
                mock_emotion = type('MockEmotion', (), scenario['emotion'])()
                
                # 感情調整を生成
                adjustments = await self.generate_emotion_speech_adjustments(
                    mock_emotion, ctx.author.id, ctx.guild.id
                )
                
                # 関係性調整を生成
                relationship_style = await self.generate_relationship_communication_style(
                    profile, ctx.author.id, ctx.guild.id
                )
                
                # 名前呼びかけ指示を生成
                name_instructions = await self.generate_name_calling_instructions(ctx, profile)
                
                await ctx.send(f"**🎭 感情調整**: {adjustments[:150]}...")
                await ctx.send(f"**💕 関係性スタイル**: {relationship_style[:150]}...")
                await ctx.send(f"**📛 名前呼びかけ**: {name_instructions[:100]}...")
                
                await asyncio.sleep(2)
            
            await ctx.send("\n✨ **感情表現テスト完了！**\n関係性を変更してもう一度試すと、異なる表現が確認できます。")
            
        except Exception as e:
            await ctx.send(f"❌ 感情テスト中にエラーが発生しました: {str(e)}")
            logger.error(f"Emotion test error: {e}")
    
    @commands.command(name='generate_feature', aliases=['gen_feat'])
    async def dev_feature(self, ctx, *, request: str):
        """Request autonomous feature development"""
        if not self.feature_manager:
            await ctx.send("❌ 自律機能開発システムは現在利用できません。")
            return
            
        # Send immediate feedback
        status_msg = await ctx.send(f"🤖 機能リクエストを受け付けました: 「{request}」\n分析と実装を開始します... (これには数分かかる場合があります)")
        
        try:
            async with ctx.typing():
                # Run in background to avoid blocking
                result = await self.feature_manager.process_feature_request(request)
            
            if result["status"] == "success":
                feature_name = result["feature_name"]
                filepath = result["filepath"]
                analysis = result["analysis"]
                code = result.get('code', '')
                
                embed = discord.Embed(
                    title=f"✨ 新機能案: {feature_name}",
                    description=analysis.get("description", "No description"),
                    color=SUCCESS_COLOR
                )
                
                embed.add_field(name="ファイルパス", value=filepath, inline=False)
                embed.add_field(name="複雑さ", value=analysis.get("complexity", "Unknown"), inline=True)
                
                if "commands" in analysis:
                    cmds = "\n".join([f"`{c['name']}`: {c['description']}" for c in analysis["commands"]])
                    embed.add_field(name="追加コマンド", value=cmds, inline=False)
                
                embed.set_footer(text="⚠️ この機能はまだロードされていません。管理者の承認が必要です。")
                
                await ctx.send(embed=embed)
                
                # Check code length and send as file if too long
                if len(code) > 1900:
                    try:
                        file = discord.File(filepath, filename=f"{feature_name}_cog.py")
                        await ctx.send("📝 生成されたコードが長いため、ファイルとして添付します:", file=file)
                    except Exception as file_e:
                        logger.error(f"Error sending file attachment: {file_e}")
                        await ctx.send(f"⚠️ ファイル添付に失敗しました。コードの一部を表示します:\n```python\n{code[:1900]}\n```\n(残りは省略されました)")
                else:
                    await ctx.send(f"実装コード:\n```python\n{code}\n```")
                
            elif result["status"] == "rejected":
                await ctx.send(f"🚫 リクエストは却下されました: {result['message']}")
            else:
                await ctx.send(f"❌ エラーが発生しました: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in dev command: {e}")
            await ctx.send(f"❌ 予期せぬエラーが発生しました: {e}")

    @commands.command(name='face_analysis', aliases=['face', 'kao'])
    async def face_analysis(self, ctx):
        """Analyze face in the attached image (!face [attach image])"""
        if not ctx.message.attachments:
            await ctx.send("❌ 画像を添付してください！")
            return
            
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ 画像ファイルを添付してください。")
            return
            
        if not self.model:
            await ctx.send("❌ AIモデルが利用できません。")
            return
            
        await ctx.send("🔍 画像を分析中... (顔の特徴、感情、年齢などを推定します)")
        
        try:
            async with ctx.typing():
                # Download image
                image_data = await attachment.read()
                
                # Prepare prompt
                prompt = """
                この画像に写っている人物の顔を詳細に分析してください。
                以下の項目について、日本語で具体的に記述してください：
                
                1. **推定年齢と性別**: (例: 20代前半の女性)
                2. **感情・表情**: (例: 楽しそうな笑顔、少し不安げな表情)
                3. **特徴**: (髪型、髪色、メガネの有無、アクセサリーなど)
                4. **印象**: (全体的な雰囲気や印象)
                """

                # Check for known faces
                known_faces = self.face_storage.get_known_faces()
                content_parts = [prompt]
                
                if known_faces:
                    prompt += "\n\nまた、以下の参照画像（known_faces）と比較し、この人物が誰であるか識別してください。\n"
                    prompt += "もし参照画像の中の人物と一致する場合は、「この人物は〇〇さんに似ています」と明記してください。\n"
                    prompt += "一致しない場合は、その旨を述べてください。"
                    
                    # Add known faces to content parts
                    # Limit to 5 faces to avoid payload limits
                    count = 0
                    for name, path in known_faces.items():
                        if count >= 5: break
                        try:
                            def _read_face(p):
                                with open(p, 'rb') as f:
                                    return f.read()
                                    
                            face_data = await asyncio.to_thread(_read_face, path)
                            content_parts.append(f"Reference: {name}")
                            content_parts.append({
                                "mime_type": "image/jpeg", # Assuming jpeg/png, Gemini handles standard formats
                                "data": face_data
                            })
                            count += 1
                        except Exception as e:
                            logger.error(f"Error reading face {name}: {e}")

                content_parts[0] = prompt # Update prompt with identification instruction
                
                # Add target image LAST
                content_parts.append("Target Image:")
                content_parts.append({
                    "mime_type": attachment.content_type,
                    "data": image_data
                })
                
                response = await self.model.generate_content_async(content_parts)
                analysis_text = response.text
                
                # Create embed
                embed = discord.Embed(
                    title="👤 顔分析・識別結果",
                    description=analysis_text,
                    color=0x00bfff
                )
                embed.set_thumbnail(url=attachment.url)
                embed.set_footer(text="Powered by Gemini Vision")
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in face analysis: {e}")
            await ctx.send(f"❌ 分析中にエラーが発生しました: {str(e)}")

    @commands.command(name='remember_face')
    async def remember_face(self, ctx, name: str):
        """Remember a face from the attached image (!remember_face name [attach image])"""
        if not ctx.message.attachments:
            await ctx.send("❌ 画像を添付してください！")
            return
            
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ 画像ファイルを添付してください。")
            return
            
        try:
            image_data = await attachment.read()
            # Determine extension
            ext = "jpg"
            if attachment.filename.lower().endswith(".png"): ext = "png"
            elif attachment.filename.lower().endswith(".webp"): ext = "webp"
            
            await self.face_storage.save_face(name, image_data, ext)
            await ctx.send(f"✅ 「{name}」さんの顔を覚えました！\n`!face` コマンドで識別できるようになります。")
            
        except Exception as e:
            logger.error(f"Error remembering face: {e}")
            await ctx.send(f"❌ 保存中にエラーが発生しました: {e}")

    @commands.command(name='load_feature')
    @commands.has_permissions(administrator=True)
    async def load_feature(self, ctx, feature_name: str):
        """Load a generated feature cog (!load_feature feature_name)"""
        try:
            # Construct module path
            module_path = f"cogs.generated.{feature_name}_cog"
            
            # Check if already loaded
            if module_path in self.bot.extensions:
                await self.bot.reload_extension(module_path)
                await ctx.send(f"🔄 機能 `{feature_name}` をリロードしました。")
            else:
                await self.bot.load_extension(module_path)
                await ctx.send(f"✅ 機能 `{feature_name}` をロードしました。")
                
        except Exception as e:
            logger.error(f"Error loading feature {feature_name}: {e}")
            await ctx.send(f"❌ 機能のロードに失敗しました: {e}")

    @commands.command(name='unload_feature')
    @commands.has_permissions(administrator=True)
    async def unload_feature(self, ctx, feature_name: str):
        """Unload a generated feature cog (!unload_feature feature_name)"""
        try:
            module_path = f"cogs.generated.{feature_name}_cog"
            
            if module_path in self.bot.extensions:
                await self.bot.unload_extension(module_path)
                await ctx.send(f"✅ 機能 `{feature_name}` をアンロードしました。")
            else:
                await ctx.send(f"⚠️ 機能 `{feature_name}` はロードされていません。")
                
        except Exception as e:
            logger.error(f"Error unloading feature {feature_name}: {e}")
            await ctx.send(f"❌ 機能のアンロードに失敗しました: {e}")

    @commands.command(name='list_features')
    @commands.has_permissions(administrator=True)
    async def list_features(self, ctx):
        """List all generated features"""
        try:
            generated_dir = "cogs/generated"
            if not os.path.exists(generated_dir):
                await ctx.send("📂 生成された機能はありません。")
                return
                
            files = [f for f in os.listdir(generated_dir) if f.endswith('_cog.py')]
            
            if not files:
                await ctx.send("📂 生成された機能はありません。")
                return
                
            embed = discord.Embed(title="🧩 生成された機能一覧", color=INFO_COLOR)
            
            for f in files:
                feature_name = f.replace('_cog.py', '')
                module_path = f"cogs.generated.{feature_name}_cog"
                status = "🟢 Loaded" if module_path in self.bot.extensions else "⚪ Unloaded"
                embed.add_field(name=feature_name, value=status, inline=True)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing features: {e}")
            await ctx.send(f"❌ エラーが発生しました: {e}")

    @commands.command(name='relationship_emotion_test')
    async def relationship_emotion_test(self, ctx):
        """関係性別の感情表現の違いを比較テスト (!relationship_emotion_test)"""
        try:
            await ctx.send("💝 **関係性別感情表現比較テスト開始...**")
            
            # テスト用の関係性レベル
            relationship_levels = ['stranger', 'friend', 'close_friend', 'intimate', 'soulmate']
            test_message = "今日は本当に疲れた..."
            test_emotion = type('MockEmotion', (), {
                "primary_emotion": "sadness",
                "energy_level": 0.2,
                "stress_level": 0.8
            })()
            
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            original_level = profile.get_custom_attribute('ai_relationship_level', 'friend')
            
            await ctx.send(f"**テストメッセージ**: {test_message}")
            await ctx.send("**各関係性レベルでの感情表現の違い**:\n")
            
            for level in relationship_levels:
                # 一時的に関係性を変更
                profile.add_custom_attribute('ai_relationship_level', level)
                
                # 感情調整を生成
                adjustments = await self.generate_emotion_speech_adjustments(
                    test_emotion, ctx.author.id, ctx.guild.id
                )
                
                # 関係性調整を生成
                relationship_style = await self.generate_relationship_communication_style(
                    profile, ctx.author.id, ctx.guild.id
                )
                
                await ctx.send(f"**{level.upper()}**: {adjustments[:120]}...")
                await asyncio.sleep(1)
            
            # 元の関係性レベルに戻す
            profile.add_custom_attribute('ai_relationship_level', original_level)
            await self.save_user_profile(profile)
            
            await ctx.send(f"\n✨ **比較テスト完了！** 関係性レベルが上がるほど、より感情豊かで親密な表現になることが確認できます。")
            
        except Exception as e:
            await ctx.send(f"❌ 関係性感情テスト中にエラーが発生しました: {str(e)}")
            logger.error(f"Relationship emotion test error: {e}")

    @commands.hybrid_command(name="stella_profile")
    async def stella_profile(self, ctx):
        """Show S.T.E.L.L.A.'s own profile and identity information"""
        try:
            profile_summary = stella_profile_manager.get_profile_summary()
            self_intro = stella_profile_manager.get_self_introduction()
            
            embed = discord.Embed(
                title="🤖 S.T.E.L.L.A. プロフィール",
                description=self_intro,
                color=0x7B68EE,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 基本情報",
                value=f"作成日: {profile_summary['creation_date'][:10]}\n"
                      f"最終更新: {profile_summary['last_updated'][:10]}\n"
                      f"人格特性: {profile_summary['personality_traits_count']}個",
                inline=True
            )
            
            embed.add_field(
                name="🎯 能力・関心",
                value=f"興味分野: {profile_summary['interests_count']}個\n"
                      f"能力: {profile_summary['capabilities_count']}個\n"
                      f"関係性: {profile_summary['relationships_count']}個",
                inline=True
            )
            
            embed.add_field(
                name="💭 記憶",
                value=f"重要な記憶: {profile_summary['memories_count']}個",
                inline=True
            )
            
            # Show family relationships
            family_info = stella_profile_manager.profile.get("relationships", {}).get("family", {})
            if family_info:
                family_text = []
                for member_key, member_data in family_info.items():
                    family_text.append(f"• {member_data['name']} ({member_data['relationship_type']})")
                
                if family_text:
                    embed.add_field(
                        name="👨‍👩‍👧‍👦 家族関係",
                        value="\n".join(family_text),
                        inline=False
                    )
            
            # Show user relationships
            user_relationships = stella_profile_manager.get_all_user_relationships()
            if user_relationships:
                user_rel_text = []
                relationship_count = 0
                
                # The structure is {user_key: user_data_dict}
                for user_key, user_data in user_relationships.items():
                    if relationship_count >= 10:  # Limit to 10 relationships for display
                        break
                    
                    if isinstance(user_data, dict) and "display_name" in user_data:
                        display_name = user_data.get("display_name", f"User {user_key}")
                        relationship_type = user_data.get("relationship_type", "friend")
                        intimacy_level = user_data.get("intimacy_level", 0)
                        conversation_count = user_data.get("conversation_count", 0)
                        
                        # Create intimacy indicator
                        intimacy_bar = "█" * (intimacy_level // 20) + "░" * (5 - (intimacy_level // 20))
                        
                        user_rel_text.append(f"• {display_name} ({relationship_type}) `{intimacy_bar}` ({conversation_count}回)")
                        relationship_count += 1
                
                if user_rel_text:
                    embed.add_field(
                        name="👥 ユーザー関係",
                        value="\n".join(user_rel_text),
                        inline=False
                    )
                    
                    total_users = len(user_relationships)
                    if total_users > relationship_count:
                        embed.add_field(
                            name="📊 関係性統計",
                            value=f"表示: {relationship_count}人 / 総計: {total_users}人",
                            inline=True
                        )
            
            embed.set_footer(text="S.T.E.L.L.A. - Smart Team Enhancement & Leisure Learning Assistant")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing S.T.E.L.L.A. profile: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="stella_memory")
    @app_commands.describe(memory_text="S.T.E.L.L.A.に記憶させたい内容")
    async def add_stella_memory(self, ctx, *, memory_text: str):
        """Add a significant memory to S.T.E.L.L.A.'s profile"""
        try:
            memory_data = {
                "content": memory_text,
                "context": f"Added by {ctx.author.display_name} in {ctx.guild.name}",
                "user_id": ctx.author.id,
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id
            }
            
            stella_profile_manager.add_memory(memory_data)
            
            embed = discord.Embed(
                title="💭 記憶を追加しました",
                description=f"記憶内容: {memory_text}",
                color=0x90EE90,
                timestamp=datetime.now()
            )
            
            embed.set_footer(text=f"追加者: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error adding S.T.E.L.L.A. memory: {e}")
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="nickname_suggest")
    @app_commands.describe(target_user="ニックネームを考えるユーザー（空白で自分）")
    async def nickname_suggest(self, ctx, target_user: Optional[discord.Member] = None):
        """Generate personalized nickname suggestions based on user profile"""
        try:
            # デフォルトは自分
            if target_user is None:
                target_user = ctx.author
            
            # プロフィール取得
            profile = await self.get_user_profile(target_user.id, ctx.guild.id)
            
            # 関係性レベル取得
            relationship_level = profile.get_custom_attribute("ai_relationship_level", "friend")
            
            # ニックネーム生成
            await ctx.send("💭 ニックネームを考えています...")
            
            nicknames = nickname_generator.generate_nicknames(
                user_profile=profile.__dict__,
                user_name=target_user.display_name,
                relationship_level=relationship_level,
                count=8
            )
            
            # 結果表示用embed作成
            embed = discord.Embed(
                title="💕 ニックネーム提案",
                description=f"{target_user.display_name}さんのためのニックネーム候補",
                color=0xFF69B4,
                timestamp=datetime.now()
            )
            
            # 現在の関係性レベル表示
            level_names = {
                "stranger": "初対面",
                "friend": "友達",
                "close": "親しい友達",
                "best_friend": "親友",
                "family": "家族",
                "intimate": "恋人",
                "soulmate": "運命の人"
            }
            
            embed.add_field(
                name="👥 関係性レベル",
                value=f"`{level_names.get(relationship_level, relationship_level)}`",
                inline=True
            )
            
            embed.add_field(
                name="📊 プロフィール情報",
                value=f"性格特性: {len(profile.personality_traits)}個\n"
                      f"興味分野: {len(profile.interests)}個\n"
                      f"カスタム属性: {len(profile.custom_attributes)}個",
                inline=True
            )
            
            # ニックネーム候補を表示
            nickname_text = []
            for i, nickname_data in enumerate(nicknames[:6], 1):
                nickname = nickname_data.get("nickname", "")
                reason = nickname_data.get("reason", "")
                type_info = nickname_data.get("type", "")
                
                # タイプに基づくアイコン
                type_icons = {
                    "name_shortening": "✂️",
                    "first_char_suffix": "🔤",
                    "personality": "🎭",
                    "interest": "🎯",
                    "relationship": "💖",
                    "special_tech": "💻",
                    "sound_variation": "🎵",
                    "fallback": "💭"
                }
                
                icon = type_icons.get(type_info, "💭")
                nickname_text.append(f"{icon} **{nickname}**\n└ {reason}")
            
            if nickname_text:
                embed.add_field(
                    name="🌟 おすすめニックネーム",
                    value="\n\n".join(nickname_text),
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌟 おすすめニックネーム",
                    value="ニックネームの生成に失敗しました。プロフィール情報を増やしてみてください。",
                    inline=False
                )
            
            # 追加のニックネーム候補があれば表示
            if len(nicknames) > 6:
                extra_nicknames = [n.get("nickname", "") for n in nicknames[6:8]]
                if extra_nicknames:
                    embed.add_field(
                        name="💡 その他の候補",
                        value=" • ".join(extra_nicknames),
                        inline=False
                    )
            
            embed.add_field(
                name="💬 使い方のヒント",
                value="関係性レベルを変更すると、より適切なニックネームが提案されます。\n"
                      "`/ai_relationship [level]` で関係性を設定できます。",
                inline=False
            )
            
            embed.set_footer(text=f"提案者: {ctx.author.display_name} | 対象: {target_user.display_name}")
            
            await ctx.send(embed=embed)
            
            # 統計更新
            stella_profile_manager.update_interaction_stats("users_helped", 1)
            
        except Exception as e:
            logger.error(f"Error generating nicknames: {e}")
            await ctx.send(f"❌ ニックネーム生成中にエラーが発生しました: {str(e)}")

    @commands.hybrid_command(name="set_nickname")
    @app_commands.describe(nickname="設定したいニックネーム")
    async def set_preferred_nickname(self, ctx, *, nickname: str):
        """Set your preferred nickname for S.T.E.L.L.A. to use"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # ニックネーム設定
            profile.add_custom_attribute("preferred_nickname", nickname)
            profile.add_custom_attribute("nickname_set_date", datetime.now().isoformat())
            profile.add_custom_attribute("nickname_set_by", "user_choice")
            
            await self.save_user_profile(profile)
            
            embed = discord.Embed(
                title="💕 ニックネーム設定完了",
                description=f"これから「**{nickname}**」と呼ばせていただきますね！",
                color=0x90EE90,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📝 設定内容",
                value=f"ニックネーム: `{nickname}`\n"
                      f"設定日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                      f"設定方法: ユーザー指定",
                inline=False
            )
            
            embed.add_field(
                name="💡 補足",
                value="今後の会話でこのニックネームを使用します。\n"
                      "変更したい場合は、再度このコマンドを使用してください。",
                inline=False
            )
            
            embed.set_footer(text=f"設定者: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
            # S.T.E.L.L.A.に記憶として追加
            memory_data = {
                "content": f"{ctx.author.display_name}さんのニックネームを「{nickname}」に設定",
                "context": f"ニックネーム設定 in {ctx.guild.name}",
                "user_id": ctx.author.id,
                "guild_id": ctx.guild.id,
                "importance": "medium"
            }
            
            stella_profile_manager.add_memory(memory_data)
            
        except Exception as e:
            logger.error(f"Error setting nickname: {e}")
            await ctx.send(f"❌ ニックネーム設定中にエラーが発生しました: {str(e)}")

    @commands.command(name="clear_nickname")
    async def clear_nickname(self, ctx):
        """現在設定されているニックネームをクリア (!clear_nickname)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Clear preferred nickname
            old_nickname = profile.get_custom_attribute("preferred_nickname", "なし")
            profile.add_custom_attribute("preferred_nickname", "")
            
            await self.save_user_profile(profile)
            
            embed = discord.Embed(
                title="🧹 ニックネームクリア完了",
                description=f"設定されていたニックネーム「{old_nickname}」をクリアしました。",
                color=0x00ff00
            )
            embed.add_field(
                name="今後の呼び方",
                value="デフォルトの名前呼びか、新しくニックネームを設定するまで通常の呼び方になります。",
                inline=False
            )
            embed.set_footer(text="新しいニックネームを設定したい場合は /nickname_suggest を使ってください")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error clearing nickname: {e}")
            await ctx.send(f"❌ ニックネームクリア中にエラーが発生しました: {str(e)}")

    @commands.command(name="fix_nickname")
    async def fix_nickname(self, ctx, user: discord.Member, *, new_nickname: str):
        """管理者用：ユーザーのニックネームを修正 (!fix_nickname @ユーザー 新しいニックネーム)"""
        # Check if user has permission (server admin or bot owner)
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == 391844907465310218):
            await ctx.send("❌ この機能は管理者のみ使用できます。")
            return
            
        try:
            profile = await self.get_user_profile(user.id, ctx.guild.id)
            
            old_nickname = profile.get_custom_attribute("preferred_nickname", "なし")
            profile.add_custom_attribute("preferred_nickname", new_nickname)
            
            await self.save_user_profile(profile)
            
            embed = discord.Embed(
                title="🔧 ニックネーム修正完了",
                description=f"{user.display_name}さんのニックネームを修正しました。",
                color=0x0099ff
            )
            embed.add_field(name="修正前", value=old_nickname, inline=True)
            embed.add_field(name="修正後", value=new_nickname, inline=True)
            embed.set_footer(text=f"修正者: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error fixing nickname: {e}")
            await ctx.send(f"❌ ニックネーム修正中にエラーが発生しました: {str(e)}")

    @commands.command(name="relationship")
    async def show_relationship_status(self, ctx):
        """現在のS.T.E.L.L.A.との関係性を表示 (!relationship)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Get relationship data
            relationship_summary_str = profile.get_custom_attribute("relationship_summary", "{}")
            try:
                relationship_summary = eval(relationship_summary_str) if relationship_summary_str else {}
                if not isinstance(relationship_summary, dict):
                    relationship_summary = {}
            except:
                relationship_summary = {}
            
            relationship_analysis_str = profile.get_custom_attribute("relationship_analysis", "{}")
            try:
                relationship_analysis = eval(relationship_analysis_str) if relationship_analysis_str else {}
                if not isinstance(relationship_analysis, dict):
                    relationship_analysis = {}
            except:
                relationship_analysis = {}
            
            try:
                intimacy_level = float(profile.get_custom_attribute("intimacy_level", "0.0"))
            except:
                intimacy_level = 0.0
            
            embed = discord.Embed(
                title="💕 S.T.E.L.L.A.との関係性",
                description=f"{ctx.author.display_name}さんとの現在の関係",
                color=0xff69b4
            )
            
            # Basic relationship info
            relationship_type = relationship_summary.get("overall_relationship_type", "友達")
            relationship_strength = relationship_summary.get("relationship_strength", 0.0)
            evolution_trend = relationship_summary.get("evolution_trend", "安定")
            
            embed.add_field(
                name="🌟 関係性のタイプ",
                value=relationship_type,
                inline=True
            )
            
            embed.add_field(
                name="💖 親密度レベル",
                value=f"{intimacy_level:.1%} ({self._get_intimacy_description(intimacy_level)})",
                inline=True
            )
            
            embed.add_field(
                name="📈 関係の変化",
                value=evolution_trend,
                inline=True
            )
            
            # Relationship strength visualization
            strength_bar = self._create_progress_bar(relationship_strength, 10)
            embed.add_field(
                name="💪 関係の強さ",
                value=f"`{strength_bar}` {relationship_strength:.1%}",
                inline=False
            )
            
            # Dominant patterns
            dominant_patterns = relationship_summary.get("dominant_patterns", [])
            if dominant_patterns:
                pattern_text = "\n".join([f"• {self._translate_pattern(pattern)}" for pattern in dominant_patterns[:3]])
                embed.add_field(
                    name="🎯 主要な関係パターン",
                    value=pattern_text,
                    inline=False
                )
            
            # Recent interaction analysis
            if relationship_analysis:
                interaction_style = relationship_analysis.get("interaction_style", [])
                if interaction_style:
                    style_text = ", ".join([self._translate_interaction_style(style) for style in interaction_style[:3]])
                    embed.add_field(
                        name="🎭 最近の交流スタイル",
                        value=style_text,
                        inline=False
                    )
            
            embed.set_footer(text="!relationship_edit で関係性を編集できます | !relationship_history で履歴を表示")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing relationship status: {e}")
            await ctx.send(f"❌ 関係性表示中にエラーが発生しました: {str(e)}")

    @commands.command(name="relationship_history")
    async def show_relationship_history(self, ctx):
        """関係性の変化履歴を表示 (!relationship_history)"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            relationship_history_str = profile.get_custom_attribute("relationship_history", "[]")
            try:
                relationship_history = eval(relationship_history_str) if relationship_history_str else []
                if not isinstance(relationship_history, list):
                    relationship_history = []
            except:
                relationship_history = []
            
            if not relationship_history:
                await ctx.send("📝 まだ関係性の履歴データがありません。S.T.E.L.L.A.ともっと会話してみてください！")
                return
            
            embed = discord.Embed(
                title="📊 関係性の変化履歴",
                description=f"{ctx.author.display_name}さんとの関係の推移",
                color=0x9370db
            )
            
            # Show last 10 entries
            recent_history = relationship_history[-10:]
            
            intimacy_values = [analysis.get("intimacy_level", 0.0) for analysis in recent_history]
            
            # Create intimacy trend visualization
            if len(intimacy_values) > 1:
                trend_text = ""
                for i, intimacy in enumerate(intimacy_values[-5:], 1):
                    bar = self._create_progress_bar(intimacy, 5)
                    trend_text += f"`{i:2}. {bar}` {intimacy:.1%}\n"
                
                embed.add_field(
                    name="💖 親密度の推移 (最新5回)",
                    value=trend_text,
                    inline=False
                )
            
            # Relationship signal frequency
            signal_counts = {}
            for analysis in recent_history:
                for signal_type, count in analysis.get("relationship_signals", {}).items():
                    signal_counts[signal_type] = signal_counts.get(signal_type, 0) + count
            
            if signal_counts:
                top_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                signal_text = "\n".join([f"• {self._translate_pattern(signal)}: {count}回" 
                                       for signal, count in top_signals])
                embed.add_field(
                    name="🎯 よく見られる関係シグナル",
                    value=signal_text,
                    inline=False
                )
            
            # Communication patterns evolution
            recent_patterns = recent_history[-1].get("communication_patterns", {}) if recent_history else {}
            if recent_patterns:
                formality = recent_patterns.get("formality_level", "casual")
                emotional = recent_patterns.get("emotional_expression", "moderate")
                
                embed.add_field(
                    name="💬 現在のコミュニケーションスタイル",
                    value=f"丁寧さ: {self._translate_formality(formality)}\n感情表現: {self._translate_emotion_level(emotional)}",
                    inline=True
                )
            
            embed.set_footer(text=f"総会話回数: {len(relationship_history)}回 | データは最新50回分保存されます")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing relationship history: {e}")
            await ctx.send(f"❌ 関係性履歴表示中にエラーが発生しました: {str(e)}")

    @commands.command(name="relationship_edit")
    async def edit_relationship(self, ctx, *, settings: str = None):
        """関係性設定を編集 (!relationship_edit [設定])"""
        try:
            if not settings:
                embed = discord.Embed(
                    title="⚙️ 関係性編集ヘルプ",
                    description="S.T.E.L.L.A.との関係性を手動で調整できます",
                    color=0xffa500
                )
                
                embed.add_field(
                    name="📝 使用方法",
                    value="!relationship_edit [設定] [値]",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 編集可能な設定",
                    value="""
                    • `type [関係タイプ]` - 友達, 恋人, 家族, 師弟関係
                    • `intimacy [0-100]` - 親密度レベル (0-100%)
                    • `nickname [ニックネーム]` - 呼び方の設定
                    • `reset` - 関係性をリセット
                    """,
                    inline=False
                )
                
                embed.add_field(
                    name="💡 例",
                    value="""
                    • `!relationship_edit type 恋人`
                    • `!relationship_edit intimacy 80`
                    • `!relationship_edit nickname ダーリン`
                    • `!relationship_edit reset`
                    """,
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            parts = settings.split()
            
            if len(parts) < 1:
                await ctx.send("❌ 設定が指定されていません。`!relationship_edit` でヘルプを確認してください。")
                return
            
            setting = parts[0].lower()
            value = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            if setting == "reset":
                # Reset relationship data
                profile.add_custom_attribute("relationship_summary", "{}")
                profile.add_custom_attribute("relationship_analysis", "{}")
                profile.add_custom_attribute("relationship_history", "[]")
                profile.add_custom_attribute("intimacy_level", "0.0")
                profile.add_custom_attribute("preferred_nickname", "")
                
                await self.save_user_profile(profile)
                
                embed = discord.Embed(
                    title="🔄 関係性リセット完了",
                    description="S.T.E.L.L.A.との関係性データをリセットしました。",
                    color=0x00ff00
                )
                embed.add_field(
                    name="📝 リセット内容",
                    value="• 関係タイプ: 友達\n• 親密度: 0%\n• ニックネーム: なし\n• 履歴: クリア",
                    inline=False
                )
                
                await ctx.send(embed=embed)
            
            elif setting == "type":
                if not value:
                    await ctx.send("❌ 関係タイプが指定されていません。")
                    return
                
                # Update relationship summary
                relationship_summary = profile.get_custom_attribute("relationship_summary", {})
                if isinstance(relationship_summary, str):
                    try:
                        relationship_summary = eval(relationship_summary)
                    except:
                        relationship_summary = {}
                
                relationship_summary["overall_relationship_type"] = value
                profile.add_custom_attribute("relationship_summary", str(relationship_summary))
                
                await self.save_user_profile(profile)
                
                await ctx.send(f"✅ 関係タイプを「{value}」に設定しました。")
            
            elif setting == "intimacy":
                try:
                    intimacy_value = float(value) / 100.0  # Convert percentage to decimal
                    intimacy_value = max(0.0, min(1.0, intimacy_value))  # Clamp to 0-1
                    
                    profile.add_custom_attribute("intimacy_level", str(intimacy_value))
                    await self.save_user_profile(profile)
                    
                    await ctx.send(f"✅ 親密度を {intimacy_value:.1%} に設定しました。")
                    
                except ValueError:
                    await ctx.send("❌ 親密度は0-100の数値で指定してください。")
            
            elif setting == "nickname":
                if not value:
                    await ctx.send("❌ ニックネームが指定されていません。")
                    return
                
                profile.add_custom_attribute("preferred_nickname", value)
                await self.save_user_profile(profile)
                
                await ctx.send(f"✅ ニックネームを「{value}」に設定しました。")
            
            else:
                await ctx.send(f"❌ 不明な設定項目: {setting}\n`!relationship_edit` でヘルプを確認してください。")
            
        except Exception as e:
            logger.error(f"Error editing relationship: {e}")
            await ctx.send(f"❌ 関係性編集中にエラーが発生しました: {str(e)}")

    def _get_intimacy_description(self, intimacy: float) -> str:
        """親密度レベルの説明を取得"""
        if intimacy >= 0.9:
            return "永遠の絆"
        elif intimacy >= 0.8:
            return "深い愛情"
        elif intimacy >= 0.7:
            return "親友以上"
        elif intimacy >= 0.5:
            return "親しい関係"
        elif intimacy >= 0.3:
            return "良い友達"
        elif intimacy >= 0.1:
            return "知り合い"
        else:
            return "初対面"

    def _create_progress_bar(self, value: float, length: int = 10) -> str:
        """プログレスバーを作成"""
        filled = int(value * length)
        empty = length - filled
        return "█" * filled + "░" * empty

    def _translate_pattern(self, pattern: str) -> str:
        """パターン名を日本語に翻訳"""
        translations = {
            "intimacy_signals": "愛情表現",
            "family_signals": "家族的関係",
            "friendship_signals": "友情",
            "respect_signals": "尊敬・憧れ",
            "care_signals": "思いやり",
            "playful_signals": "遊び心",
            "dependency_signals": "依存・甘え"
        }
        return translations.get(pattern, pattern)

    def _translate_interaction_style(self, style: str) -> str:
        """交流スタイルを日本語に翻訳"""
        translations = {
            "affectionate": "愛情深い",
            "playful": "遊び心のある",
            "protective": "保護的",
            "admiring": "尊敬する",
            "dependent": "甘える",
            "supportive": "支援的"
        }
        return translations.get(style, style)

    def _translate_formality(self, formality: str) -> str:
        """丁寧さレベルを日本語に翻訳"""
        translations = {
            "formal": "とても丁寧",
            "polite": "丁寧",
            "casual": "カジュアル",
            "intimate": "親密"
        }
        return translations.get(formality, formality)

    def _translate_emotion_level(self, emotion: str) -> str:
        """感情表現レベルを日本語に翻訳"""
        translations = {
            "low": "控えめ",
            "moderate": "適度",
            "high": "豊か",
            "intense": "情熱的"
        }
        return translations.get(emotion, emotion)

    async def analyze_and_store_relationship_dynamics(self, ctx, user_message: str, ai_response: str):
        """Enhanced relationship analysis and storage"""
        try:
            profile = await self.get_user_profile(ctx.author.id, ctx.guild.id)
            
            # Get current relationship data
            current_relationship_str = profile.get_custom_attribute("relationship_analysis", "{}")
            try:
                current_relationship = eval(current_relationship_str) if current_relationship_str else {}
                if not isinstance(current_relationship, dict):
                    current_relationship = {}
            except:
                current_relationship = {}
            
            # Analyze relationship from conversation
            relationship_analysis = relationship_analyzer.analyze_relationship_from_conversation(
                user_message, ai_response, current_relationship
            )
            
            if relationship_analysis:
                # Store relationship analysis history
                relationship_history_str = profile.get_custom_attribute("relationship_history", "[]")
                try:
                    relationship_history = eval(relationship_history_str) if relationship_history_str else []
                    if not isinstance(relationship_history, list):
                        relationship_history = []
                except:
                    relationship_history = []
                
                relationship_history.append(relationship_analysis)
                
                # Keep only last 50 analyses to prevent bloat
                if len(relationship_history) > 50:
                    relationship_history = relationship_history[-50:]
                
                profile.add_custom_attribute("relationship_history", str(relationship_history))
                profile.add_custom_attribute("relationship_analysis", str(relationship_analysis))
                
                # Generate relationship summary
                relationship_summary = relationship_analyzer.generate_relationship_summary(relationship_history)
                if relationship_summary:
                    profile.add_custom_attribute("relationship_summary", str(relationship_summary))
                
                # Update intimacy level based on analysis
                intimacy_level = relationship_analysis.get("intimacy_level", 0.0)
                profile.add_custom_attribute("intimacy_level", str(intimacy_level))
                
                # Store dominant relationship signals
                signals = relationship_analysis.get("relationship_signals", {})
                if signals:
                    profile.add_custom_attribute("dominant_relationship_signals", str(signals))
                
                await self.save_user_profile(profile)
                
                logger.info(f"Relationship dynamics analyzed and stored for user {ctx.author.id}")
                
        except Exception as e:
            logger.error(f"Error analyzing relationship dynamics: {e}")

    def detect_nickname_request(self, message: str) -> str:
        """Detect nickname requests in user messages"""
        import re
        
        # Pattern for "〜って呼んで" or "〜と呼んで" 
        patterns = [
            r'私を(.+?)って呼んで',
            r'私を(.+?)と呼んで',
            r'俺を(.+?)って呼んで',
            r'俺を(.+?)と呼んで',
            r'僕を(.+?)って呼んで',
            r'僕を(.+?)と呼んで',
            r'(.+?)って呼んで',
            r'(.+?)と呼んで', 
            r'(.+?)って呼んでください',
            r'(.+?)と呼んでください',
            r'(.+?)って呼ばれたい',
            r'(.+?)と呼ばれたい',
            r'call me (.+)',
            r'名前は(.+?)です',
            r'(.+?)でお願いします'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                nickname = match.group(1).strip()
                # Clean up the nickname
                nickname = nickname.replace('「', '').replace('」', '')
                nickname = nickname.replace('"', '').replace("'", '')
                nickname = nickname.strip()
                
                # Validate nickname (not too long, no special characters that might break things)
                if len(nickname) <= 20 and nickname:
                    return nickname
        
        return None

    def determine_relationship_type(self, profile) -> str:
        """Determine relationship type for S.T.E.L.L.A.'s tracking"""
        try:
            # Check if user is creator/developer
            if profile.get_custom_attribute("is_creator", False) or "creator" in str(profile.custom_attributes).lower():
                return "creator"
            
            # Check relationship level
            relationship_level = profile.get_custom_attribute("ai_relationship_level", "friend")
            if relationship_level in ["best_friend", "soulmate", "intimate"]:
                return "close_friend"
            elif relationship_level in ["mentor", "teacher"]:
                return "mentor"
            elif relationship_level in ["student"]:
                return "student"
            else:
                return "friend"
        except:
            return "friend"
    
    def calculate_intimacy_level(self, profile) -> int:
        """Calculate intimacy level for S.T.E.L.L.A.'s tracking"""
        try:
            intimacy = 0
            
            # Base on interaction history
            interaction_count = len(profile.interaction_history)
            intimacy += min(50, interaction_count * 2)
            
            # Base on relationship level
            relationship_level = profile.get_custom_attribute("ai_relationship_level", "friend")
            level_values = {
                "stranger": 0, "acquaintance": 10, "friend": 30,
                "close": 50, "best_friend": 70, "intimate": 85, "soulmate": 95
            }
            intimacy += level_values.get(relationship_level, 30)
            
            # Base on personal information shared
            personal_info_count = len(profile.interests) + len(profile.personality_traits)
            intimacy += min(20, personal_info_count * 2)
            
            return min(100, intimacy)
        except:
            return 30
    
    def determine_communication_style(self, profile) -> str:
        """Determine communication style for S.T.E.L.L.A.'s tracking"""
        try:
            # Analyze personality traits
            traits = profile.personality_traits or []
            trait_text = " ".join(traits).lower()
            
            if any(word in trait_text for word in ["明るい", "元気", "活発", "cheerful"]):
                return "energetic"
            elif any(word in trait_text for word in ["優しい", "穏やか", "親切", "kind"]):
                return "gentle"
            elif any(word in trait_text for word in ["真面目", "丁寧", "正直", "serious"]):
                return "formal"
            else:
                return "friendly"
        except:
            return "friendly"
    
    def extract_memorable_moment(self, user_message: str, ai_response: str) -> str:
        """Extract memorable moments from conversation"""
        try:
            # Check for special keywords that indicate memorable moments
            memorable_keywords = [
                "初めて", "特別", "大切", "忘れない", "覚えて", "思い出",
                "嬉しい", "楽しい", "感動", "驚き", "好き", "愛"
            ]
            
            combined_text = user_message + " " + ai_response
            
            for keyword in memorable_keywords:
                if keyword in combined_text:
                    # Extract context around the keyword
                    sentences = combined_text.split("。")
                    for sentence in sentences:
                        if keyword in sentence and len(sentence.strip()) > 10:
                            return sentence.strip()[:100]
            
            # If no special keywords, check for longer interactions
            if len(user_message) > 50 or len(ai_response) > 100:
                return f"深い会話: {user_message[:50]}..."
            
            return ""
        except:
            return ""

    async def update_stella_relationship_tracking(self, ctx, user_message: str, ai_response: str, profile):
        """Update S.T.E.L.L.A.'s user relationship tracking"""
        try:
            from utils.stella_profile_manager import stella_profile_manager
            
            # Prepare user data for S.T.E.L.L.A.'s relationship tracking
            user_relationship_data = {
                "display_name": ctx.author.display_name,
                "nickname": profile.nickname or "",
                "relationship_type": self.determine_relationship_type(profile),
                "intimacy_level": self.calculate_intimacy_level(profile),
                "personality_notes": ", ".join(profile.personality_traits[:3]) if profile.personality_traits else "",
                "shared_interests": profile.interests[:3] if profile.interests else [],
                "communication_style": self.determine_communication_style(profile),
                "memorable_moment": self.extract_memorable_moment(user_message, ai_response),
                "moment_context": f"Conversation on {datetime.now().strftime('%Y-%m-%d')}"
            }
            
            # Update S.T.E.L.L.A.'s user relationship data
            stella_profile_manager.update_user_relationship(
                ctx.author.id, 
                ctx.guild.id, 
                user_relationship_data
            )
            
            logger.info(f"Updated S.T.E.L.L.A.'s relationship data for user {ctx.author.id}")
        except Exception as e:
            logger.error(f"Error updating S.T.E.L.L.A. relationship data: {e}")

    async def generate_nickname_context(self, ctx, profile) -> str:
        """Generate nickname context for conversation prompts"""
        try:
            # Check if user has set a preferred nickname
            preferred_nickname = profile.nickname or profile.get_custom_attribute("preferred_nickname", "")
            if preferred_nickname:
                return f"\n\n【ニックネーム指定】このユーザーを「{preferred_nickname}」と呼んでください。これは相手が設定した希望するニックネームです。自然に使用してください。"
            
            # Check relationship level for auto-suggestion
            relationship_level = profile.get_custom_attribute("ai_relationship_level", "friend")
            
            # Only suggest nicknames for closer relationships
            if relationship_level in ["close", "best_friend", "family", "intimate", "soulmate"]:
                try:
                    # Generate appropriate nickname suggestions
                    suggested_nicknames = nickname_generator.generate_nicknames(
                        user_profile=profile.__dict__,
                        user_name=ctx.author.display_name,
                        relationship_level=relationship_level,
                        count=2
                    )
                    
                    if suggested_nicknames:
                        best_nickname = suggested_nicknames[0].get("nickname", "")
                        # Only use short, natural nicknames
                        if best_nickname and len(best_nickname) <= 6 and not any(char in best_nickname for char in ["プログラマー", "エンジニア", "博士"]):
                            return f"\n\n【関係性ベースニックネーム】{relationship_level}関係なので、適切な場合は「{best_nickname}」のような親しみやすい呼び方を使っても良いです。ただし自然な文脈でのみ使用し、強制的ではありません。"
                    
                except Exception as e:
                    logger.error(f"Error generating nickname suggestions: {e}")
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating nickname context: {e}")
            return ""
    
    async def process_voice_command(self, user_id: int, guild_id: int, text: str) -> str:
        """音声コマンドを処理してAI応答を生成"""
        try:
            # Get guild and user objects
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return "サーバーが見つかりません"
            
            user = guild.get_member(user_id)
            if not user:
                return "ユーザーが見つかりません"
            
            # Get or create profile
            profile = self.profile_storage.get_profile(user_id, guild_id)
            if not profile:
                profile = self.profile_storage.create_profile(user_id, guild_id)
                profile.display_name = user.display_name
                profile.username = user.name
            
            # Generate AI response using existing conversation system
            prompt = self._build_conversation_prompt(profile, text)
            
            if self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                ai_response = response.text.strip()
            else:
                ai_response = "音声認識は成功しましたが、AIシステムが利用できません"
            
            # Update conversation history
            if hasattr(profile, 'conversation_history'):
                profile.conversation_history.append({
                    'user': text,
                    'ai': ai_response,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'voice'
                })
            
            # Save profile updates
            self.profile_storage.save_profile(profile)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return f"音声コマンド処理中にエラーが発生しました: {str(e)}"

async def setup(bot):
    await bot.add_cog(AICog(bot))