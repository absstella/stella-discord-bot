"""
Temporary file-based profile storage system
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional
from database.models import UserProfile
import logging

logger = logging.getLogger(__name__)

class ProfileStorage:
    """File-based profile storage for when database is unavailable"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Profile storage initialized: {data_dir}")
    
    def _get_profile_path(self, user_id: int, guild_id: int) -> str:
        """Get file path for user profile"""
        return os.path.join(self.data_dir, f"profile_{guild_id}_{user_id}.json")
    
    def save_profile(self, profile: UserProfile) -> bool:
        """Save profile to file"""
        try:
            file_path = self._get_profile_path(profile.user_id, profile.guild_id)
            profile_data = profile.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Profile saved for user {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, user_id: int, guild_id: int) -> Optional[UserProfile]:
        """Load profile from file"""
        try:
            file_path = self._get_profile_path(user_id, guild_id)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            for date_field in ['created_at', 'updated_at', 'last_updated']:
                if data.get(date_field):
                    data[date_field] = datetime.fromisoformat(data[date_field])
            
            # Create UserProfile from loaded data
            profile = UserProfile(
                user_id=data['user_id'],
                guild_id=data['guild_id'],
                nickname=data.get('nickname'),
                description=data.get('description'),
                personality_traits=data.get('personality_traits', []),
                interests=data.get('interests', []),
                favorite_games=data.get('favorite_games', []),
                memorable_moments=data.get('memorable_moments', []),
                custom_attributes=data.get('custom_attributes', {}),
                conversation_patterns=data.get('conversation_patterns', []),
                emotional_context=data.get('emotional_context', {}),
                interaction_history=data.get('interaction_history', []),
                learned_preferences=data.get('learned_preferences', {}),
                speech_patterns=data.get('speech_patterns', {}),
                reaction_patterns=data.get('reaction_patterns', {}),
                relationship_context=data.get('relationship_context', {}),
                behavioral_traits=data.get('behavioral_traits', []),
                communication_style=data.get('communication_style', {}),
                auto_extracted_info=data.get('auto_extracted_info', {}),
                communication_styles=data.get('communication_styles', {}),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at'),
                last_updated=data.get('last_updated')
            )
            
            logger.info(f"Profile loaded for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return None
    
    def get_all_profiles(self, guild_id: int) -> Dict[int, UserProfile]:
        """Get all profiles for a guild"""
        profiles = {}
        try:
            for filename in os.listdir(self.data_dir):
                if filename.startswith(f"profile_{guild_id}_") and filename.endswith(".json"):
                    user_id = int(filename.split('_')[2].split('.')[0])
                    profile = self.load_profile(user_id, guild_id)
                    if profile:
                        profiles[user_id] = profile
        except Exception as e:
            logger.error(f"Error loading all profiles: {e}")
        
        return profiles

# Global instance
profile_storage = ProfileStorage()