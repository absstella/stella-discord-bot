import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add bot root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.profile_storage import profile_storage

def verify_fix():
    user_id = 391844907465310218
    guild_id = 643982855122321443
    
    print(f"Attempting to load profile for user {user_id} in guild {guild_id}...")
    
    profile = profile_storage.load_profile(user_id, guild_id)
    
    if profile:
        print("\n✅ Profile loaded successfully!")
        print(f"Nickname: {profile.nickname}")
        print(f"Description: {profile.description}")
        print(f"Traits: {profile.personality_traits}")
        return True
    else:
        print("\n❌ Failed to load profile.")
        return False

if __name__ == "__main__":
    verify_fix()
