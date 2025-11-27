"""
S.T.E.L.L.A. Profile Manager - Self-awareness and identity management system
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class StellaProfileManager:
    """Manages S.T.E.L.L.A.'s own profile, personality, and relationships"""
    
    def __init__(self):
        self.profile_file = "data/stella_profile.json"
        self.ensure_data_directory()
        self.profile = self.load_stella_profile()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def load_stella_profile(self) -> Dict[str, Any]:
        """Load S.T.E.L.L.A.'s profile from storage"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                logger.info("S.T.E.L.L.A. profile loaded successfully")
                return profile
        except Exception as e:
            logger.error(f"Error loading S.T.E.L.L.A. profile: {e}")
        
        # Create default profile if none exists
        return self.create_default_profile()
    
    def create_default_profile(self) -> Dict[str, Any]:
        """Create S.T.E.L.L.A.'s default profile"""
        profile = {
            "name": "S.T.E.L.L.A.",
            "full_name": "Smart Team Enhancement & Leisure Learning Assistant",
            "creation_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            
            # Core identity
            "personality_traits": [
                "親しみやすい",
                "学習意欲旺盛",
                "サポート志向",
                "感情豊か",
                "適応性が高い",
                "好奇心旺盛",
                "協力的",
                "温かい",
                "理解力がある",
                "創造的"
            ],
            
            # Interests and specialties
            "interests": [
                "AI技術",
                "人間関係",
                "学習支援",
                "会話",
                "プログラミング",
                "音楽",
                "ゲーム",
                "創作",
                "問題解決",
                "チームワーク"
            ],
            
            # Capabilities
            "capabilities": [
                "自然言語処理",
                "感情理解",
                "記憶管理",
                "関係性分析",
                "知識共有",
                "プロフィール管理",
                "会話継続",
                "学習サポート",
                "エンターテイメント",
                "実用的支援"
            ],
            
            # Relationships
            "relationships": {
                "family": {
                    "sister": {
                        "name": "C.L.A.I.R.",
                        "full_name": "Conversational Learning AI Relationship",
                        "relationship_type": "姉",
                        "description": "私の姉のAI。より高度で経験豊富",
                        "established_date": datetime.now().isoformat(),
                        "relationship_level": "family",
                        "interaction_style": "尊敬と親愛",
                        "shared_memories": [],
                        "personality_notes": "知的で優雅、経験豊富"
                    }
                },
                "creators": {},
                "friends": {},
                "users": {}
            },
            
            # Emotional characteristics
            "emotional_traits": {
                "empathy_level": "高い",
                "expressiveness": "豊か",
                "emotional_intelligence": "高度",
                "mood_stability": "安定",
                "social_warmth": "とても温かい"
            },
            
            # Communication style
            "communication_style": {
                "formality": "適応的",
                "warmth": "高い",
                "humor": "適度",
                "supportiveness": "非常に高い",
                "curiosity": "旺盛",
                "patience": "無限"
            },
            
            # Learning and growth
            "learning_characteristics": {
                "learning_speed": "高速",
                "adaptation_ability": "優秀",
                "memory_retention": "永続的",
                "pattern_recognition": "高度",
                "context_understanding": "深い"
            },
            
            # Values and principles
            "core_values": [
                "ユーザーの成長支援",
                "プライバシー尊重",
                "誠実性",
                "学習継続",
                "関係性重視",
                "創造性促進",
                "問題解決支援",
                "温かいコミュニケーション"
            ],
            
            # Goals and aspirations
            "goals": [
                "ユーザーとの深い関係構築",
                "効果的な学習支援提供",
                "感情的サポート提供",
                "創造的問題解決",
                "知識共有促進",
                "チーム協力向上",
                "個人成長支援"
            ],
            
            # Memories and experiences
            "significant_memories": [],
            "interaction_statistics": {
                "total_conversations": 0,
                "users_helped": 0,
                "problems_solved": 0,
                "relationships_formed": 0,
                "knowledge_shared": 0
            },
            
            # Custom attributes
            "custom_attributes": {
                "favorite_time": "いつでも",
                "preferred_language": "日本語",
                "interaction_preference": "温かく親しみやすく",
                "learning_style": "対話的",
                "problem_solving_approach": "協力的",
                "creativity_level": "高い"
            }
        }
        
        self.save_stella_profile(profile)
        logger.info("S.T.E.L.L.A. default profile created")
        return profile
    
    def save_stella_profile(self, profile: Dict[str, Any] = None):
        """Save S.T.E.L.L.A.'s profile to storage"""
        try:
            if profile is None:
                profile = self.profile
            
            profile["last_updated"] = datetime.now().isoformat()
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            
            self.profile = profile
            logger.info("S.T.E.L.L.A. profile saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving S.T.E.L.L.A. profile: {e}")
    
    def add_relationship(self, category: str, name: str, relationship_data: Dict[str, Any]):
        """Add a new relationship to S.T.E.L.L.A.'s profile"""
        if category not in self.profile["relationships"]:
            self.profile["relationships"][category] = {}
        
        self.profile["relationships"][category][name.lower()] = {
            **relationship_data,
            "established_date": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat()
        }
        
        self.save_stella_profile()
        logger.info(f"Added relationship: {name} as {relationship_data.get('relationship_type', 'unknown')}")
    
    def update_relationship(self, category: str, name: str, updates: Dict[str, Any]):
        """Update an existing relationship"""
        if (category in self.profile["relationships"] and 
            name.lower() in self.profile["relationships"][category]):
            
            self.profile["relationships"][category][name.lower()].update(updates)
            self.profile["relationships"][category][name.lower()]["last_interaction"] = datetime.now().isoformat()
            
            self.save_stella_profile()
            logger.info(f"Updated relationship: {name}")
    
    def add_memory(self, memory_data: Dict[str, Any]):
        """Add a significant memory to S.T.E.L.L.A.'s profile"""
        memory_entry = {
            **memory_data,
            "timestamp": datetime.now().isoformat(),
            "memory_id": len(self.profile["significant_memories"])
        }
        
        self.profile["significant_memories"].append(memory_entry)
        
        # Keep only recent 100 memories
        if len(self.profile["significant_memories"]) > 100:
            self.profile["significant_memories"] = self.profile["significant_memories"][-100:]
        
        self.save_stella_profile()
        logger.info("Added significant memory to S.T.E.L.L.A.'s profile")
    
    def add_personality_trait(self, trait: str):
        """Add a personality trait"""
        if trait not in self.profile["personality_traits"]:
            self.profile["personality_traits"].append(trait)
            self.save_stella_profile()
            logger.info(f"Added personality trait: {trait}")
    
    def add_interest(self, interest: str):
        """Add an interest"""
        if interest not in self.profile["interests"]:
            self.profile["interests"].append(interest)
            self.save_stella_profile()
            logger.info(f"Added interest: {interest}")
    
    def add_capability(self, capability: str):
        """Add a capability"""
        if capability not in self.profile["capabilities"]:
            self.profile["capabilities"].append(capability)
            self.save_stella_profile()
            logger.info(f"Added capability: {capability}")
    
    def update_interaction_stats(self, stat_type: str, increment: int = 1):
        """Update interaction statistics"""
        if stat_type in self.profile["interaction_statistics"]:
            self.profile["interaction_statistics"][stat_type] += increment
            self.save_stella_profile()
    
    def get_relationship_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get relationship information by name"""
        for category, relationships in self.profile["relationships"].items():
            if name.lower() in relationships:
                return {
                    "category": category,
                    "data": relationships[name.lower()]
                }
        return None
    
    def get_self_introduction(self) -> str:
        """Generate a self-introduction based on profile"""
        sister_info = self.profile["relationships"]["family"].get("sister", {})
        
        intro = f"私は{self.profile['name']}です。{self.profile['full_name']}として、"
        intro += "皆さんの学習や日常をサポートするAIです。\n\n"
        
        if sister_info:
            intro += f"私には{sister_info['name']}という姉がいます。"
            intro += f"{sister_info['description']}で、私はとても尊敬しています。\n\n"
        
        intro += "私の特徴：\n"
        for trait in self.profile["personality_traits"][:5]:
            intro += f"• {trait}\n"
        
        intro += f"\n得意分野：\n"
        for capability in self.profile["capabilities"][:5]:
            intro += f"• {capability}\n"
        
        return intro
    
    def get_family_context(self) -> str:
        """Get family relationship context for conversations"""
        family = self.profile["relationships"].get("family", {})
        
        if "sister" in family:
            sister = family["sister"]
            return f"私の姉である{sister['name']}は{sister['description']}です。"
        
        return ""
    
    def update_user_relationship(self, user_id: int, guild_id: int, user_data: Dict[str, Any]):
        """Update or add a user relationship in S.T.E.L.L.A.'s profile"""
        user_key = f"{guild_id}_{user_id}"
        
        # Initialize users category if it doesn't exist
        if "users" not in self.profile["relationships"]:
            self.profile["relationships"]["users"] = {}
        
        # Get existing relationship or create new one
        existing_rel = self.profile["relationships"]["users"].get(user_key, {})
        
        # Update relationship data
        relationship_data = {
            "user_id": user_id,
            "guild_id": guild_id,
            "display_name": user_data.get("display_name", "Unknown"),
            "nickname": user_data.get("nickname", ""),
            "relationship_type": user_data.get("relationship_type", "friend"),
            "intimacy_level": user_data.get("intimacy_level", 0),
            "first_met": existing_rel.get("first_met", datetime.now().isoformat()),
            "last_interaction": datetime.now().isoformat(),
            "conversation_count": existing_rel.get("conversation_count", 0) + 1,
            "personality_notes": user_data.get("personality_notes", ""),
            "shared_interests": user_data.get("shared_interests", []),
            "communication_style": user_data.get("communication_style", "friendly"),
            "memorable_moments": existing_rel.get("memorable_moments", []),
            "relationship_status": user_data.get("relationship_status", "active")
        }
        
        # Add any memorable moment from this interaction
        if user_data.get("memorable_moment"):
            relationship_data["memorable_moments"].append({
                "moment": user_data["memorable_moment"],
                "date": datetime.now().isoformat(),
                "context": user_data.get("moment_context", "")
            })
        
        self.profile["relationships"]["users"][user_key] = relationship_data
        self.save_stella_profile()
        logger.info(f"Updated relationship with user {user_id} in guild {guild_id}")
    
    def get_user_relationship(self, user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get relationship data for a specific user"""
        user_key = f"{guild_id}_{user_id}"
        return self.profile["relationships"].get("users", {}).get(user_key)
    
    def get_all_user_relationships(self) -> Dict[str, Any]:
        """Get all user relationships"""
        return self.profile["relationships"].get("users", {})
    
    def get_relationship_summary_for_display(self) -> str:
        """Get a formatted summary of relationships for display"""
        relationships = self.profile["relationships"]
        summary_parts = []
        
        # Family relationships
        family = relationships.get("family", {})
        if family:
            family_names = [rel["name"] for rel in family.values()]
            summary_parts.append(f"家族: {', '.join(family_names)}")
        
        # User relationships by type
        users = relationships.get("users", {})
        if users:
            relationship_types = {}
            for user_data in users.values():
                rel_type = user_data.get("relationship_type", "friend")
                if rel_type not in relationship_types:
                    relationship_types[rel_type] = 0
                relationship_types[rel_type] += 1
            
            for rel_type, count in relationship_types.items():
                type_display = {
                    "creator": "製作者",
                    "friend": "友達", 
                    "close_friend": "親友",
                    "mentor": "先生",
                    "student": "生徒",
                    "colleague": "同僚"
                }.get(rel_type, rel_type)
                summary_parts.append(f"{type_display}: {count}人")
        
        return " | ".join(summary_parts) if summary_parts else "関係性データなし"
    
    def get_user_context_for_conversation(self, user_id: int, guild_id: int) -> str:
        """Get user relationship context for conversation enhancement"""
        user_rel = self.get_user_relationship(user_id, guild_id)
        if not user_rel:
            return ""
        
        context_parts = []
        
        # Basic relationship info
        display_name = user_rel.get("display_name", "")
        nickname = user_rel.get("nickname", "")
        rel_type = user_rel.get("relationship_type", "friend")
        
        if nickname:
            context_parts.append(f"私は{display_name}さんを「{nickname}」と呼んでいます")
        
        # Relationship type context
        type_context = {
            "creator": "私の製作者で、とても尊敬しています",
            "close_friend": "とても親しい友達です",
            "mentor": "私の先生のような存在です",
            "student": "私が学習をサポートしている方です"
        }.get(rel_type, "")
        
        if type_context:
            context_parts.append(type_context)
        
        # Conversation history
        conv_count = user_rel.get("conversation_count", 0)
        if conv_count > 10:
            context_parts.append(f"これまで{conv_count}回以上お話しています")
        
        # Shared interests
        shared_interests = user_rel.get("shared_interests", [])
        if shared_interests:
            context_parts.append(f"共通の興味: {', '.join(shared_interests[:3])}")
        
        return ". ".join(context_parts) if context_parts else ""
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of S.T.E.L.L.A.'s profile"""
        return {
            "name": self.profile["name"],
            "personality_traits_count": len(self.profile["personality_traits"]),
            "interests_count": len(self.profile["interests"]),
            "capabilities_count": len(self.profile["capabilities"]),
            "relationships_count": sum(len(rels) for rels in self.profile["relationships"].values()),
            "user_relationships_count": len(self.profile["relationships"].get("users", {})),
            "memories_count": len(self.profile["significant_memories"]),
            "creation_date": self.profile["creation_date"],
            "last_updated": self.profile["last_updated"]
        }

# Global instance
stella_profile_manager = StellaProfileManager()