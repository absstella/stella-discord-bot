"""
Guild Knowledge Storage System
Manages shared knowledge base for Discord guilds
"""
import os
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from database.models import GuildKnowledge

logger = logging.getLogger(__name__)

class GuildKnowledgeStorage:
    """Manages guild-wide shared knowledge storage"""
    
    def __init__(self, base_path: str = "data/guild_knowledge"):
        self.base_path = base_path
        self.knowledge_cache: Dict[int, Dict[str, GuildKnowledge]] = {}
        self._ensure_directory_exists()
        logger.info(f"Guild Knowledge Storage initialized: {base_path}")
    
    def _ensure_directory_exists(self):
        """Ensure the guild knowledge directory exists"""
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_guild_file_path(self, guild_id: int) -> str:
        """Get the file path for a specific guild's knowledge"""
        return os.path.join(self.base_path, f"guild_{guild_id}.json")
    
    def _load_guild_knowledge(self, guild_id: int) -> Dict[str, GuildKnowledge]:
        """Load knowledge for a specific guild"""
        if guild_id in self.knowledge_cache:
            return self.knowledge_cache[guild_id]
        
        file_path = self._get_guild_file_path(guild_id)
        knowledge_dict = {}
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for knowledge_id, knowledge_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'created_at' in knowledge_data and isinstance(knowledge_data['created_at'], str):
                        knowledge_data['created_at'] = datetime.fromisoformat(knowledge_data['created_at'])
                    if 'updated_at' in knowledge_data and isinstance(knowledge_data['updated_at'], str):
                        knowledge_data['updated_at'] = datetime.fromisoformat(knowledge_data['updated_at'])
                    if 'last_accessed' in knowledge_data and isinstance(knowledge_data['last_accessed'], str):
                        knowledge_data['last_accessed'] = datetime.fromisoformat(knowledge_data['last_accessed'])
                    
                    knowledge_dict[knowledge_id] = GuildKnowledge(**knowledge_data)
                
                logger.info(f"Loaded {len(knowledge_dict)} knowledge items for guild {guild_id}")
            except Exception as e:
                logger.error(f"Error loading guild knowledge for {guild_id}: {e}")
        
        self.knowledge_cache[guild_id] = knowledge_dict
        return knowledge_dict
    
    def _save_guild_knowledge(self, guild_id: int):
        """Save knowledge for a specific guild"""
        if guild_id not in self.knowledge_cache:
            return
        
        file_path = self._get_guild_file_path(guild_id)
        knowledge_dict = self.knowledge_cache[guild_id]
        
        try:
            # Convert to serializable format
            serializable_data = {}
            for knowledge_id, knowledge in knowledge_dict.items():
                knowledge_data = {
                    'guild_id': knowledge.guild_id,
                    'knowledge_id': knowledge.knowledge_id,
                    'category': knowledge.category,
                    'title': knowledge.title,
                    'content': knowledge.content,
                    'tags': knowledge.tags,
                    'contributors': knowledge.contributors,
                    'importance_score': knowledge.importance_score,
                    'last_accessed': knowledge.last_accessed.isoformat(),
                    'created_at': knowledge.created_at.isoformat(),
                    'updated_at': knowledge.updated_at.isoformat(),
                    'source_channel_id': knowledge.source_channel_id,
                    'source_message_id': knowledge.source_message_id
                }
                serializable_data[knowledge_id] = knowledge_data
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(knowledge_dict)} knowledge items for guild {guild_id}")
        except Exception as e:
            logger.error(f"Error saving guild knowledge for {guild_id}: {e}")
    
    async def add_knowledge(self, guild_id: int, category: str, title: str, content: str, 
                           contributor_id: int, tags: List[str] = None, 
                           importance_score: float = 1.0, source_channel_id: int = None,
                           source_message_id: int = None, auto_generated: bool = False) -> str:
        """Add new knowledge to guild knowledge base"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        
        knowledge_id = str(uuid.uuid4())
        knowledge = GuildKnowledge(
            guild_id=guild_id,
            knowledge_id=knowledge_id,
            category=category,
            title=title,
            content=content,
            tags=tags or [],
            contributors=[contributor_id],
            importance_score=importance_score,
            source_channel_id=source_channel_id,
            source_message_id=source_message_id
        )
        
        knowledge_dict[knowledge_id] = knowledge
        self.knowledge_cache[guild_id] = knowledge_dict
        self._save_guild_knowledge(guild_id)
        
        logger.info(f"Added new knowledge '{title}' to guild {guild_id}")
        return knowledge_id
    
    async def get_knowledge(self, guild_id: int, knowledge_id: str) -> Optional[GuildKnowledge]:
        """Get specific knowledge item"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        knowledge = knowledge_dict.get(knowledge_id)
        
        if knowledge:
            knowledge.update_access_time()
            self._save_guild_knowledge(guild_id)
        
        return knowledge
    
    async def search_knowledge(self, guild_id: int, query: str = None, category: str = None, 
                              tags: List[str] = None, limit: int = 10) -> List[GuildKnowledge]:
        """Search guild knowledge base"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        results = []
        
        for knowledge in knowledge_dict.values():
            match_score = 0
            
            # Category filter
            if category and knowledge.category.lower() != category.lower():
                continue
            
            # Tags filter
            if tags:
                if not any(tag.lower() in [t.lower() for t in knowledge.tags] for tag in tags):
                    continue
                match_score += 2
            
            # Text search
            if query:
                query_lower = query.lower()
                if query_lower in knowledge.title.lower():
                    match_score += 5
                if query_lower in knowledge.content.lower():
                    match_score += 3
                if any(query_lower in tag.lower() for tag in knowledge.tags):
                    match_score += 2
                
                # Skip if no text match found
                if match_score == 0:
                    continue
            
            # Add importance score to match score
            match_score += knowledge.importance_score
            
            results.append((match_score, knowledge))
        
        # Sort by match score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        final_results = [knowledge for _, knowledge in results[:limit]]
        
        # Update access times
        for knowledge in final_results:
            knowledge.update_access_time()
        
        if final_results:
            self._save_guild_knowledge(guild_id)
        
        return final_results
    
    async def update_knowledge(self, guild_id: int, knowledge_id: str, 
                              title: str = None, content: str = None, 
                              category: str = None, tags: List[str] = None,
                              importance_score: float = None,
                              contributor_id: int = None) -> bool:
        """Update existing knowledge item"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        
        if knowledge_id not in knowledge_dict:
            return False
        
        knowledge = knowledge_dict[knowledge_id]
        
        if title:
            knowledge.title = title
        if content:
            knowledge.content = content
        if category:
            knowledge.category = category
        if tags is not None:
            knowledge.tags = tags
        if importance_score is not None:
            knowledge.importance_score = importance_score
        if contributor_id:
            knowledge.add_contributor(contributor_id)
        
        knowledge.updated_at = datetime.utcnow()
        self._save_guild_knowledge(guild_id)
        
        logger.info(f"Updated knowledge '{knowledge.title}' in guild {guild_id}")
        return True
    
    async def delete_knowledge(self, guild_id: int, knowledge_id: str) -> bool:
        """Delete knowledge item"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        
        if knowledge_id in knowledge_dict:
            title = knowledge_dict[knowledge_id].title
            del knowledge_dict[knowledge_id]
            self._save_guild_knowledge(guild_id)
            logger.info(f"Deleted knowledge '{title}' from guild {guild_id}")
            return True
        
        return False
    
    async def get_all_categories(self, guild_id: int) -> List[str]:
        """Get all categories in guild knowledge base"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        categories = set()
        
        for knowledge in knowledge_dict.values():
            categories.add(knowledge.category)
        
        return sorted(list(categories))
    
    async def get_knowledge_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get statistics about guild knowledge base"""
        knowledge_dict = self._load_guild_knowledge(guild_id)
        
        if not knowledge_dict:
            return {
                'total_items': 0,
                'categories': {},
                'top_contributors': {},
                'recent_items': []
            }
        
        # Count by category
        categories = {}
        contributors = {}
        
        for knowledge in knowledge_dict.values():
            # Category count
            if knowledge.category not in categories:
                categories[knowledge.category] = 0
            categories[knowledge.category] += 1
            
            # Contributor count
            for contributor_id in knowledge.contributors:
                if contributor_id not in contributors:
                    contributors[contributor_id] = 0
                contributors[contributor_id] += 1
        
        # Get recent items (last 5)
        recent_items = sorted(
            knowledge_dict.values(),
            key=lambda k: k.created_at,
            reverse=True
        )[:5]
        
        # Sort contributors by contribution count
        top_contributors = dict(sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'total_items': len(knowledge_dict),
            'categories': categories,
            'top_contributors': top_contributors,
            'recent_items': [
                {
                    'title': item.title,
                    'category': item.category,
                    'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for item in recent_items
            ]
        }
    
    async def get_relevant_knowledge_for_context(self, guild_id: int, context: str, 
                                                max_items: int = 5) -> List[GuildKnowledge]:
        """Get knowledge items relevant to conversation context"""
        # This is a simplified relevance search
        # In a more advanced system, this could use embedding-based similarity
        
        knowledge_dict = self._load_guild_knowledge(guild_id)
        if not knowledge_dict:
            return []
        
        context_lower = context.lower()
        relevant_items = []
        
        for knowledge in knowledge_dict.values():
            relevance_score = 0
            
            # Check title relevance
            if any(word in knowledge.title.lower() for word in context_lower.split()):
                relevance_score += 3
            
            # Check content relevance
            if any(word in knowledge.content.lower() for word in context_lower.split()):
                relevance_score += 2
            
            # Check tag relevance
            if any(word in tag.lower() for tag in knowledge.tags for word in context_lower.split()):
                relevance_score += 2
            
            # Add importance score
            relevance_score += knowledge.importance_score * 0.5
            
            if relevance_score > 0:
                relevant_items.append((relevance_score, knowledge))
        
        # Sort by relevance and return top items
        relevant_items.sort(key=lambda x: x[0], reverse=True)
        results = [knowledge for _, knowledge in relevant_items[:max_items]]
        
        # Update access times
        for knowledge in results:
            knowledge.update_access_time()
        
        if results:
            self._save_guild_knowledge(guild_id)
        
        return results