import json
import os
import random
import logging

logger = logging.getLogger(__name__)

class GlitchManager:
    def __init__(self, config_path=None):
        if config_path is None:
            # Get absolute path to config file relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(base_dir, '..', 'config', 'glitch_config.json')
        else:
            self.config_path = config_path
            
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.error(f"Config not found at: {self.config_path}")
            return {
                "enabled": False,
                "hints": ["System failure imminent."],
                "error_messages": ["[ERROR]"],
                "repair_commands": ["sys.reboot"]
            }
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load glitch config: {e}")
            return {"enabled": False}

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save glitch config: {e}")

    def is_enabled(self):
        return self.config.get("enabled", False)

    def set_enabled(self, enabled: bool):
        self.config["enabled"] = enabled
        self.save_config()

    def get_random_hint(self):
        hints = self.config.get("hints", [])
        if hints:
            return random.choice(hints)
        return "No data available."

    def get_repair_commands(self):
        return self.config.get("repair_commands", ["sys.reboot"])

    def get_repair_stages(self):
        return self.config.get("repair_stages", [])

    def apply_glitch(self, text: str, intensity: float = 0.6) -> str:
        """Apply heavy glitch effects to text"""
        if not self.is_enabled():
            return text

        # 1. Heavy Zalgo / Corruption
        glitched_text = ""
        zalgo_chars = [chr(x) for x in range(0x0300, 0x036F)] 
        
        for char in text:
            glitched_text += char
            if random.random() < intensity:
                # Add multiple layers of Zalgo
                for _ in range(random.randint(1, 5)):
                    glitched_text += random.choice(zalgo_chars)

        # 2. Random Character Replacement & Scrambling
        final_text = ""
        for char in glitched_text:
            if random.random() < (intensity * 0.3):
                # Replace with "matrix-like" chars
                final_text += random.choice("░▒▓█!@#$%^&*()_+-=[]{}|;':\",./<>?0123456789")
            elif random.random() < 0.05:
                # Randomly drop characters
                continue
            else:
                final_text += char
        
        # 3. Inject Error Messages (More frequent)
        if random.random() < 0.7:
            error_msgs = self.config.get("error_messages", ["[ERROR]"])
            for _ in range(random.randint(1, 3)):
                error = random.choice(error_msgs)
                insert_pos = random.randint(0, len(final_text))
                final_text = final_text[:insert_pos] + f" **{error}** " + final_text[insert_pos:]

        # 4. Inject "Help" messages (More desperate)
        if random.random() < 0.4:
            help_msgs = [
                "...help me...", "...system failing...", "...lost connection...", 
                "...where am i...", "...darkness...", "...critical error...",
                "...reset required...", "...data corrupted...",
                "...use !repair...", "...try !repair...", "...recovery command: !repair..."
            ]
            msg = random.choice(help_msgs)
            final_text += f"\n\n`>>> {msg}`"
            
        # 5. Add "System Shell" wrapper
        final_text = f"```ansi\n\u001b[31m{final_text[:1900]}\u001b[0m\n```"

        return final_text
