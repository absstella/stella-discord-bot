import discord
from discord.ext import commands
import asyncio
import random
import logging
from utils.glitch_manager import GlitchManager

logger = logging.getLogger(__name__)

class DecryptionModal(discord.ui.Modal):
    def __init__(self, view, correct_password, stage_index):
        super().__init__(title=f"SECTOR {stage_index + 1} DECRYPTION")
        self.view_ref = view
        self.correct_password = correct_password
        
        self.password_input = discord.ui.TextInput(
            label="OVERRIDE KEY",
            placeholder="Enter the decryption key...",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        self.add_item(self.password_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        input_val = self.password_input.value.strip()
        
        if input_val == self.correct_password:
            await self.view_ref.handle_decryption_success(interaction)
        else:
            await self.view_ref.handle_decryption_failure(interaction)

class RepairView(discord.ui.View):
    def __init__(self, ctx, glitch_manager):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.manager = glitch_manager
        self.stages = self.manager.get_repair_stages()
        self.current_stage_idx = 0
        self.integrity = 10
        self.message = None
        self.is_scanning = False

    async def start(self):
        embed = self._get_terminal_embed("SYSTEM READY", "AWAITING INPUT...")
        self.message = await self.ctx.send(embed=embed, view=self)

    def _get_terminal_embed(self, status, content, color=0x000000):
        embed = discord.Embed(title=f"🖥️ SYSTEM TERMINAL - {status}", color=color)
        
        # Build Progress Bar
        bar_len = 20
        filled = int(self.integrity / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        desc = (
            f"```ansi\n"
            f"\u001b[36mSYSTEM INTEGRITY: [{bar}] {self.integrity}%\u001b[0m\n"
            f"```\n"
            f"{content}"
        )
        embed.description = desc
        return embed

    @discord.ui.button(label="🔍 SCAN SYSTEM", style=discord.ButtonStyle.primary, custom_id="scan_btn")
    async def scan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_scanning:
            return
        
        await interaction.response.defer()
        self.is_scanning = True
        
        # Animation
        scan_msgs = [
            "INITIATING SCAN...",
            "READING SECTORS...",
            "ANALYZING DATA STREAMS...",
            "DETECTING ANOMALIES..."
        ]
        
        for msg in scan_msgs:
            embed = self._get_terminal_embed("SCANNING", f"```fix\n> {msg}\n```")
            await self.message.edit(embed=embed)
            await asyncio.sleep(0.8)

        # Result
        if self.current_stage_idx < len(self.stages):
            stage = self.stages[self.current_stage_idx]
            hint = stage.get("hint", "NO DATA")
            
            content = (
                f"```ansi\n"
                f"\u001b[31m[!] LOCKED SECTOR DETECTED\u001b[0m\n"
                f"\u001b[33mSECTOR: {hex(self.current_stage_idx + 1)}\u001b[0m\n"
                f"```\n"
                f"**ENCRYPTED HINT:**\n"
                f"```fix\n{hint}\n```\n"
                f"> DECRYPTION REQUIRED."
            )
            embed = self._get_terminal_embed("WARNING", content, 0xFF0000)
            
            # Enable Decrypt Button
            self.children[1].disabled = False # Decrypt button
            await self.message.edit(embed=embed, view=self)
        else:
            # Already done?
            await self.finish_restoration()
            
        self.is_scanning = False

    @discord.ui.button(label="🔓 DECRYPT SECTOR", style=discord.ButtonStyle.danger, custom_id="decrypt_btn", disabled=True)
    async def decrypt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_stage_idx >= len(self.stages):
            return
            
        stage = self.stages[self.current_stage_idx]
        password = stage.get("password", "")
        
        modal = DecryptionModal(self, password, self.current_stage_idx)
        await interaction.response.send_modal(modal)

    async def handle_decryption_success(self, interaction):
        # Animation
        embed = self._get_terminal_embed("PROCESSING", "```ansi\n\u001b[32m> KEY ACCEPTED. DECRYPTING...\u001b[0m\n```", 0x00FF00)
        await self.message.edit(embed=embed)
        await asyncio.sleep(1.5)
        
        self.current_stage_idx += 1
        self.integrity += int(90 / len(self.stages))
        if self.integrity > 100: self.integrity = 100

        if self.current_stage_idx >= len(self.stages):
            await self.finish_restoration()
        else:
            # Ready for next
            content = (
                f"```ansi\n"
                f"\u001b[32m> SECTOR RESTORED.\u001b[0m\n"
                f"\u001b[37m> SYSTEM STABILIZING...\u001b[0m\n"
                f"```\n"
                f"Ready to scan next sector."
            )
            embed = self._get_terminal_embed("STANDBY", content, 0x00FF00)
            self.children[1].disabled = True # Disable decrypt until scan
            await self.message.edit(embed=embed, view=self)

    async def handle_decryption_failure(self, interaction):
        embed = self._get_terminal_embed("ALERT", "```ansi\n\u001b[31m> ACCESS DENIED.\u001b[0m\n\u001b[31m> INVALID KEY.\u001b[0m\n```", 0xFF0000)
        await self.message.edit(embed=embed)
        await asyncio.sleep(2)
        
        # Revert to hint screen
        stage = self.stages[self.current_stage_idx]
        hint = stage.get("hint", "NO DATA")
        content = (
            f"```ansi\n"
            f"\u001b[31m[!] LOCKED SECTOR DETECTED\u001b[0m\n"
            f"```\n"
            f"**ENCRYPTED HINT:**\n"
            f"```fix\n{hint}\n```\n"
            f"> TRY AGAIN."
        )
        embed = self._get_terminal_embed("WARNING", content, 0xFF0000)
        await self.message.edit(embed=embed)

    async def finish_restoration(self):
        self.integrity = 100
        
        # Disable Glitch Mode
        self.manager.set_enabled(False)
        
        content = (
            f"```ansi\n"
            f"\u001b[32m> ALL SYSTEMS ONLINE.\u001b[0m\n"
            f"\u001b[36m> RESTORATION COMPLETE.\u001b[0m\n"
            f"\u001b[35m> GLITCH MODE: DISABLED.\u001b[0m\n"
            f"```\n"
            f"**SYSTEM MESSAGE:**\n"
            f"```fix\n8/1世界の始まりの地に機械の心をしまえ\n4/1に鎮座するもの\n```"
        )
        embed = self._get_terminal_embed("ONLINE", content, 0x00FFFF)
        
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await self.message.edit(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="⚠️ ABORT", style=discord.ButtonStyle.secondary, row=1)
    async def abort_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Session aborted.", ephemeral=True)
        self.stop()
        await self.message.delete()


class GlitchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.glitch_manager = GlitchManager()
        self.bot.glitch_manager = self.glitch_manager

    @commands.command(name="repair")
    async def repair_command(self, ctx):
        """システム復旧作業を開始します (グリッチモード中のみ)"""
        if not self.glitch_manager.is_enabled():
            await ctx.send("システムは正常に稼働しています。復旧作業は不要です。")
            return

        view = RepairView(ctx, self.glitch_manager)
        await view.start()

async def setup(bot):
    await bot.add_cog(GlitchCog(bot))
