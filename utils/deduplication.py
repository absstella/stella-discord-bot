import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set, Dict, Optional
import weakref

logger = logging.getLogger(__name__)

class DeduplicationManager:
    """
    Manages deduplication of commands and messages to prevent spam and conflicts.
    Uses weak references and time-based cleanup to manage memory efficiently.
    """
    
    def __init__(self, cleanup_interval: int = 300):
        self.executing_commands: Set[int] = set()
        self.command_timestamps: Dict[int, datetime] = {}
        self.user_cooldowns: Dict[int, Dict[str, datetime]] = {}
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = datetime.utcnow()
        
        # Command-specific cooldowns (in seconds)
        self.command_cooldowns = {
            'play': 3,
            'ask': 5,
            'search': 10,
            'vmap': 2,
            'vagent': 2,
            'recruit': 30,
            'teams': 10,
            'poll': 60
        }

    def is_command_executing(self, message_id: int) -> bool:
        """Check if a command is currently executing for this message"""
        return message_id in self.executing_commands

    def start_command_execution(self, message_id: int) -> bool:
        """
        Mark a command as executing.
        Returns True if successfully marked, False if already executing.
        """
        if message_id in self.executing_commands:
            return False
        
        self.executing_commands.add(message_id)
        self.command_timestamps[message_id] = datetime.utcnow()
        return True

    def end_command_execution(self, message_id: int):
        """Mark a command as finished executing"""
        self.executing_commands.discard(message_id)
        self.command_timestamps.pop(message_id, None)

    def is_user_on_cooldown(self, user_id: int, command: str) -> bool:
        """Check if a user is on cooldown for a specific command"""
        if user_id not in self.user_cooldowns:
            return False
        
        if command not in self.user_cooldowns[user_id]:
            return False
        
        cooldown_duration = self.command_cooldowns.get(command, 0)
        if cooldown_duration == 0:
            return False
        
        last_used = self.user_cooldowns[user_id][command]
        cooldown_end = last_used + timedelta(seconds=cooldown_duration)
        
        return datetime.utcnow() < cooldown_end

    def get_user_cooldown_remaining(self, user_id: int, command: str) -> float:
        """Get remaining cooldown time in seconds for a user and command"""
        if not self.is_user_on_cooldown(user_id, command):
            return 0.0
        
        cooldown_duration = self.command_cooldowns.get(command, 0)
        last_used = self.user_cooldowns[user_id][command]
        cooldown_end = last_used + timedelta(seconds=cooldown_duration)
        
        remaining = (cooldown_end - datetime.utcnow()).total_seconds()
        return max(0.0, remaining)

    def set_user_cooldown(self, user_id: int, command: str):
        """Set cooldown for a user and command"""
        if user_id not in self.user_cooldowns:
            self.user_cooldowns[user_id] = {}
        
        self.user_cooldowns[user_id][command] = datetime.utcnow()

    async def cleanup(self):
        """Clean up old entries to prevent memory leaks"""
        try:
            current_time = datetime.utcnow()
            
            # Only cleanup if enough time has passed
            if (current_time - self.last_cleanup).total_seconds() < self.cleanup_interval:
                return
            
            # Clean up old command timestamps (older than 1 hour)
            cutoff_time = current_time - timedelta(hours=1)
            old_commands = [
                cmd_id for cmd_id, timestamp in self.command_timestamps.items()
                if timestamp < cutoff_time
            ]
            
            for cmd_id in old_commands:
                self.executing_commands.discard(cmd_id)
                self.command_timestamps.pop(cmd_id, None)
            
            # Clean up old user cooldowns (older than max cooldown time)
            max_cooldown = max(self.command_cooldowns.values()) if self.command_cooldowns else 300
            cooldown_cutoff = current_time - timedelta(seconds=max_cooldown * 2)
            
            users_to_clean = []
            for user_id, commands in self.user_cooldowns.items():
                commands_to_remove = [
                    cmd for cmd, timestamp in commands.items()
                    if timestamp < cooldown_cutoff
                ]
                
                for cmd in commands_to_remove:
                    commands.pop(cmd, None)
                
                # Remove user entry if no commands left
                if not commands:
                    users_to_clean.append(user_id)
            
            for user_id in users_to_clean:
                self.user_cooldowns.pop(user_id, None)
            
            self.last_cleanup = current_time
            
            # Log cleanup statistics
            if old_commands or users_to_clean:
                logger.debug(f"Deduplication cleanup: removed {len(old_commands)} old commands, "
                           f"{len(users_to_clean)} empty user cooldown entries")
                
        except Exception as e:
            logger.error(f"Error during deduplication cleanup: {e}")

    def get_stats(self) -> Dict:
        """Get current deduplication statistics"""
        return {
            'executing_commands': len(self.executing_commands),
            'tracked_command_timestamps': len(self.command_timestamps),
            'users_with_cooldowns': len(self.user_cooldowns),
            'total_active_cooldowns': sum(len(commands) for commands in self.user_cooldowns.values()),
            'last_cleanup': self.last_cleanup.isoformat()
        }

    def force_cleanup_user(self, user_id: int):
        """Force cleanup all cooldowns for a specific user"""
        self.user_cooldowns.pop(user_id, None)

    def force_cleanup_command(self, message_id: int):
        """Force cleanup a specific command execution"""
        self.executing_commands.discard(message_id)
        self.command_timestamps.pop(message_id, None)

    def set_command_cooldown(self, command: str, cooldown_seconds: int):
        """Dynamically set cooldown for a command"""
        self.command_cooldowns[command] = cooldown_seconds

    def remove_command_cooldown(self, command: str):
        """Remove cooldown for a command"""
        self.command_cooldowns.pop(command, None)

    def reset_all_cooldowns(self):
        """Reset all user cooldowns (admin function)"""
        self.user_cooldowns.clear()
        logger.info("All user cooldowns have been reset")

    def get_user_cooldown_status(self, user_id: int) -> Dict[str, float]:
        """Get all active cooldowns for a user"""
        if user_id not in self.user_cooldowns:
            return {}
        
        status = {}
        for command in self.user_cooldowns[user_id]:
            remaining = self.get_user_cooldown_remaining(user_id, command)
            if remaining > 0:
                status[command] = remaining
        
        return status
