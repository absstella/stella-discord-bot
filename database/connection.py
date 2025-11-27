import os
import asyncio
import logging
from typing import Optional, AsyncContextManager
import asyncpg
from asyncpg import Pool, Connection
from contextlib import asynccontextmanager
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations.
    Provides connection pooling and automatic reconnection.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.pool: Optional[Pool] = None
        self._initialized = False
        self._connection_attempts = 0
        self.max_connection_attempts = 5

    async def initialize(self):
        """Initialize the database connection pool"""
        if self._initialized:
            return
        
        if not self.database_url:
            logger.error("Database URL not provided")
            return
        
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'stella_bot',
                }
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
            
            # Create tables
            await self.create_tables()
            
            self._initialized = True
            self._connection_attempts = 0
            logger.info("Database initialized successfully")
            
        except Exception as e:
            self._connection_attempts += 1
            logger.error(f"Failed to initialize database (attempt {self._connection_attempts}/{self.max_connection_attempts}): {e}")
            
            if self._connection_attempts < self.max_connection_attempts:
                # Retry after delay
                await asyncio.sleep(5)
                await self.initialize()
            else:
                logger.error("Max database connection attempts reached. Database features will be unavailable.")

    async def create_tables(self):
        """Create database tables if they don't exist"""
        if not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                # User statistics table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id BIGINT PRIMARY KEY,
                        wins INTEGER DEFAULT 0,
                        losses INTEGER DEFAULT 0,
                        total_kda REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Birthdays table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS birthdays (
                        user_id BIGINT PRIMARY KEY,
                        birth_date DATE NOT NULL,
                        guild_id BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Reminders table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL,
                        reminder_time TIMESTAMP NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Guild settings table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS guild_settings (
                        guild_id BIGINT PRIMARY KEY,
                        prefix VARCHAR(10) DEFAULT '!',
                        music_channel_id BIGINT,
                        announcement_channel_id BIGINT,
                        birthday_channel_id BIGINT,
                        auto_delete_music_messages BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Music queue history (for analytics)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS music_history (
                        id SERIAL PRIMARY KEY,
                        guild_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        song_title TEXT NOT NULL,
                        song_url TEXT NOT NULL,
                        duration INTEGER,
                        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # AI conversation logs (for analytics)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS ai_conversations (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        message_content TEXT NOT NULL,
                        response_content TEXT NOT NULL,
                        tokens_used INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User profiles table for memory system
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        nickname TEXT,
                        description TEXT,
                        personality_traits TEXT DEFAULT '[]',
                        interests TEXT DEFAULT '[]',
                        favorite_games TEXT DEFAULT '[]',
                        memorable_moments TEXT DEFAULT '[]',
                        custom_attributes TEXT DEFAULT '{}',
                        conversation_patterns TEXT DEFAULT '[]',
                        emotional_context TEXT DEFAULT '{}',
                        interaction_history TEXT DEFAULT '[]',
                        learned_preferences TEXT DEFAULT '{}',
                        speech_patterns TEXT DEFAULT '{}',
                        reaction_patterns TEXT DEFAULT '{}',
                        relationship_context TEXT DEFAULT '{}',
                        behavioral_traits TEXT DEFAULT '[]',
                        communication_style TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, guild_id)
                    )
                ''')
                
                # Add new columns if they don't exist (for existing databases)
                try:
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS conversation_patterns TEXT DEFAULT \'[]\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS emotional_context TEXT DEFAULT \'{}\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS interaction_history TEXT DEFAULT \'[]\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS learned_preferences TEXT DEFAULT \'{}\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS speech_patterns TEXT DEFAULT \'{}\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS reaction_patterns TEXT DEFAULT \'{}\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS relationship_context TEXT DEFAULT \'{}\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS behavioral_traits TEXT DEFAULT \'[]\'')
                    await conn.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS communication_style TEXT DEFAULT \'{}\'')
                except Exception as e:
                    logger.debug(f"Column addition failed (may already exist): {e}")
                
                # Create indexes for better performance
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_birthdays_guild_id ON birthdays(guild_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_birthdays_birth_date ON birthdays(birth_date)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_reminder_time ON reminders(reminder_time)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_music_history_guild_id ON music_history(guild_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_music_history_played_at ON music_history(played_at)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_ai_conversations_created_at ON ai_conversations(created_at)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_profiles_guild_id ON user_profiles(guild_id)')
                
                logger.info("Database tables created/verified successfully")
                
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database operation error: {e}")
                raise

    async def execute_query(self, query: str, *args) -> str:
        """Execute a query and return the result status"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    async def fetch_one(self, query: str, *args):
        """Fetch a single row"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def fetch_value(self, query: str, *args):
        """Fetch a single value"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)

    def is_connected(self) -> bool:
        """Check if database is connected and available"""
        return self._initialized and self.pool is not None

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.pool:
                return False
            
            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
            return True
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        if not self.pool:
            return {}
        
        return {
            'size': self.pool.get_size(),
            'min_size': self.pool.get_min_size(),
            'max_size': self.pool.get_max_size(),
            'idle_size': self.pool.get_idle_size(),
            'closed': self.pool.is_closing()
        }

    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            logger.info("Database connection pool closed")

    async def backup_user_data(self, user_id: int) -> dict:
        """Backup all data for a specific user"""
        try:
            async with self.get_connection() as conn:
                # Get user stats
                user_stats = await conn.fetchrow(
                    "SELECT * FROM user_stats WHERE user_id = $1", user_id
                )
                
                # Get user birthdays
                birthdays = await conn.fetch(
                    "SELECT * FROM birthdays WHERE user_id = $1", user_id
                )
                
                # Get user reminders
                reminders = await conn.fetch(
                    "SELECT * FROM reminders WHERE user_id = $1", user_id
                )
                
                # Get user music history
                music_history = await conn.fetch(
                    "SELECT * FROM music_history WHERE user_id = $1 ORDER BY played_at DESC LIMIT 100",
                    user_id
                )
                
                # Get user AI conversations
                ai_conversations = await conn.fetch(
                    "SELECT * FROM ai_conversations WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100",
                    user_id
                )
                
                return {
                    'user_id': user_id,
                    'user_stats': dict(user_stats) if user_stats else None,
                    'birthdays': [dict(row) for row in birthdays],
                    'reminders': [dict(row) for row in reminders],
                    'music_history': [dict(row) for row in music_history],
                    'ai_conversations': [dict(row) for row in ai_conversations],
                    'backup_timestamp': asyncio.get_event_loop().time()
                }
                
        except Exception as e:
            logger.error(f"Error backing up user data for {user_id}: {e}")
            return {}

    async def delete_user_data(self, user_id: int) -> dict:
        """Delete all data for a specific user (GDPR compliance)"""
        try:
            deleted_counts = {}
            
            async with self.get_connection() as conn:
                # Delete from each table and count deletions
                deleted_counts['user_stats'] = await conn.execute(
                    "DELETE FROM user_stats WHERE user_id = $1", user_id
                )
                
                deleted_counts['birthdays'] = await conn.execute(
                    "DELETE FROM birthdays WHERE user_id = $1", user_id
                )
                
                deleted_counts['reminders'] = await conn.execute(
                    "DELETE FROM reminders WHERE user_id = $1", user_id
                )
                
                deleted_counts['music_history'] = await conn.execute(
                    "DELETE FROM music_history WHERE user_id = $1", user_id
                )
                
                deleted_counts['ai_conversations'] = await conn.execute(
                    "DELETE FROM ai_conversations WHERE user_id = $1", user_id
                )
                
                logger.info(f"Deleted user data for {user_id}: {deleted_counts}")
                return deleted_counts
                
        except Exception as e:
            logger.error(f"Error deleting user data for {user_id}: {e}")
            return {}

# Global database manager instance
db_manager = DatabaseManager()

# Compatibility function for legacy imports
async def get_db_connection():
    """Get database connection for backward compatibility"""
    return db_manager.get_connection()
