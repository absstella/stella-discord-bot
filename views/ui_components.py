import asyncio
import logging
from typing import Dict, List, Optional, Callable
import discord
from discord.ext import commands
from data.help_data import HELP_DATA
from config import *

logger = logging.getLogger(__name__)

class HelpView(discord.ui.View):
    """Help menu with dropdown selection"""
    
    def __init__(self, bot, author):
        super().__init__(timeout=300)
        self.bot = bot
        self.author = author
        self.add_item(HelpDropdown(bot))

    def get_initial_embed(self):
        """Get the initial help embed"""
        embed = discord.Embed(
            title="📋 S.T.E.L.L.A. コマンド一覧",
            description="下のメニューからカテゴリを選択してください。\n各カテゴリのコマンド一覧が表示されます。",
            color=0x00ff00
        )
        embed.set_footer(text=f"Requested by {self.author.display_name}")
        return embed

class HelpDropdown(discord.ui.Select):
    """Dropdown menu for help categories"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Define categories
        self.categories = {
            "ai": {"label": "AI・会話", "emoji": "🤖", "desc": "AIチャット、質問、検索"},
            "profile": {"label": "プロフィール", "emoji": "👤", "desc": "ユーザープロフィールの管理"},
            "knowledge": {"label": "共有知識", "emoji": "📚", "desc": "サーバー固有の知識管理"},
            "voice": {"label": "音声・音楽", "emoji": "🎵", "desc": "読み上げ、音楽再生"},
            "creative": {"label": "クリエイティブ", "emoji": "🎨", "desc": "画像生成、創作支援"},
            "game": {"label": "ゲーム", "emoji": "🎮", "desc": "ゲーム連携、サイコロ"},
            "dev": {"label": "開発・進化", "emoji": "⚙️", "desc": "新機能開発、システム進化"},
            "utility": {"label": "ユーティリティ", "emoji": "🛠️", "desc": "その他便利機能"}
        }
        
        options = []
        for key, data in self.categories.items():
            options.append(discord.SelectOption(
                label=data["label"],
                description=data["desc"],
                emoji=data["emoji"],
                value=key
            ))
        
        super().__init__(
            placeholder="カテゴリを選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        category_data = self.categories.get(category_key)
        
        if not category_data:
            return

        # Collect commands for this category
        commands_list = []
        for cog_name, cog in self.bot.cogs.items():
            for command in cog.get_commands():
                if command.hidden:
                    continue
                
                # Categorize logic (same as utility_cog)
                cat = "utility"
                if command.name in ['generate_feature', 'dev', 'evolve', 'trigger_evolution']:
                    cat = "dev"
                else:
                    cog_name_lower = cog_name.lower()
                    if 'music' in cog_name_lower or 'voice' in cog_name_lower:
                        cat = "voice"
                    elif 'image' in cog_name_lower or 'draw' in cog_name_lower:
                        cat = "creative"
                    elif 'ai' in cog_name_lower or 'chat' in cog_name_lower:
                        cat = "ai"
                    elif 'profile' in cog_name_lower:
                        cat = "profile"
                    elif 'knowledge' in cog_name_lower:
                        cat = "knowledge"
                    elif 'game' in cog_name_lower or 'minecraft' in cog_name_lower:
                        cat = "game"
                    elif 'dev' in cog_name_lower or 'evolution' in cog_name_lower:
                        cat = "dev"
                
                if cat == category_key:
                    commands_list.append(command)
        
        # Create embed
        embed = discord.Embed(
            title=f"{category_data['emoji']} {category_data['label']} コマンド",
            description=f"{category_data['desc']}に関するコマンド一覧です。",
            color=0x00ff00
        )
        
        if commands_list:
            # Sort by name
            commands_list.sort(key=lambda x: x.name)
            
            for cmd in commands_list:
                aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                # Use docstring first line as help
                help_text = cmd.help.split('\n')[0] if cmd.help else "説明なし"
                embed.add_field(
                    name=f"`!{cmd.name}{aliases}`",
                    value=help_text,
                    inline=False
                )
        else:
            embed.description = "このカテゴリにはコマンドがありません。"
            
        await interaction.response.edit_message(embed=embed, view=self.view)




class RecruitmentView(discord.ui.View):
    """Team recruitment interface"""
    
    def __init__(self, game: str, max_members: int, author: discord.Member):
        super().__init__(timeout=300)
        self.game = game
        self.max_members = max_members
        self.author = author
        self.participants = [author]

    @discord.ui.button(label="🎮 Join", style=discord.ButtonStyle.success)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Join the recruitment"""
        try:
            if interaction.user in self.participants:
                await interaction.response.send_message("❌ You're already in this team!", ephemeral=True)
                return
            
            if len(self.participants) >= self.max_members:
                await interaction.response.send_message("❌ Team is full!", ephemeral=True)
                return
            
            self.participants.append(interaction.user)
            
            # Update embed
            embed = discord.Embed(
                title=f"🎮 {self.game.upper()} - Team Recruitment",
                description=f"**Leader:** {self.author.mention}\n**Slots:** {len(self.participants)}/{self.max_members}",
                color=EMBED_COLOR
            )
            
            participants_text = ""
            for i, participant in enumerate(self.participants):
                role = " (Leader)" if participant == self.author else ""
                participants_text += f"{i+1}. {participant.display_name}{role}\n"
            
            embed.add_field(
                name="📝 Participants",
                value=participants_text,
                inline=False
            )
            
            # Check if team is full
            if len(self.participants) >= self.max_members:
                embed.color = SUCCESS_COLOR
                embed.add_field(
                    name="✅ Team Complete!",
                    value="All slots have been filled. Good luck with your game!",
                    inline=False
                )
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
            
            embed.set_footer(text="Click below to join or leave!")
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            if len(self.participants) < self.max_members:
                await interaction.followup.send(f"✅ {interaction.user.mention} joined the team!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Join button error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)

    @discord.ui.button(label="🚪 Leave", style=discord.ButtonStyle.secondary)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Leave the recruitment"""
        try:
            if interaction.user not in self.participants:
                await interaction.response.send_message("❌ You're not in this team!", ephemeral=True)
                return
            
            if interaction.user == self.author:
                # Leader is leaving, cancel recruitment
                embed = discord.Embed(
                    title=f"❌ {self.game.upper()} - Recruitment Cancelled",
                    description="The team leader has left. Recruitment has been cancelled.",
                    color=ERROR_COLOR
                )
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)
                return
            
            self.participants.remove(interaction.user)
            
            # Update embed
            embed = discord.Embed(
                title=f"🎮 {self.game.upper()} - Team Recruitment",
                description=f"**Leader:** {self.author.mention}\n**Slots:** {len(self.participants)}/{self.max_members}",
                color=EMBED_COLOR
            )
            
            participants_text = ""
            for i, participant in enumerate(self.participants):
                role = " (Leader)" if participant == self.author else ""
                participants_text += f"{i+1}. {participant.display_name}{role}\n"
            
            embed.add_field(
                name="📝 Participants",
                value=participants_text,
                inline=False
            )
            
            embed.set_footer(text="Click below to join or leave!")
            
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"👋 {interaction.user.mention} left the team!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Leave button error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)

class PollView(discord.ui.View):
    """Poll voting interface"""
    
    def __init__(self, options: List[str], author: discord.Member):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.options = options
        self.author = author
        self.votes: Dict[str, List[discord.Member]] = {option: [] for option in options}
        
        # Add buttons for each option
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, option in enumerate(options[:10]):  # Max 10 options
            button = PollButton(option, emojis[i], i)
            self.add_item(button)

    def get_results_embed(self) -> discord.Embed:
        """Generate results embed"""
        embed = discord.Embed(
            title="📊 Poll Results",
            color=EMBED_COLOR
        )
        
        total_votes = sum(len(voters) for voters in self.votes.values())
        
        results_text = ""
        for i, (option, voters) in enumerate(self.votes.items()):
            vote_count = len(voters)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            # Create progress bar
            bar_length = 10
            filled_length = int(percentage / 10)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            results_text += f"{emojis[i]} **{option}**\n"
            results_text += f"`{bar}` {vote_count} votes ({percentage:.1f}%)\n\n"
        
        embed.description = results_text
        embed.add_field(
            name="📈 Total Votes",
            value=str(total_votes),
            inline=True
        )
        
        embed.set_footer(text=f"Poll by {self.author.display_name}")
        
        return embed

class PollButton(discord.ui.Button):
    """Individual poll option button"""
    
    def __init__(self, option: str, emoji: str, index: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=option[:80],  # Discord button label limit
            emoji=emoji,
            custom_id=f"poll_option_{index}"
        )
        self.option = option

    async def callback(self, interaction: discord.Interaction):
        """Handle poll vote"""
        try:
            poll_view = self.view
            user = interaction.user
            
            # Remove user's previous vote
            for option, voters in poll_view.votes.items():
                if user in voters:
                    voters.remove(user)
            
            # Add new vote
            poll_view.votes[self.option].append(user)
            
            # Update message with results
            embed = poll_view.get_results_embed()
            await interaction.response.edit_message(embed=embed, view=poll_view)
            
        except Exception as e:
            logger.error(f"Poll button error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)

class ConfirmationView(discord.ui.View):
    """Generic confirmation dialog"""
    
    def __init__(self, author: discord.Member, callback_confirm: Callable, callback_cancel: Callable = None):
        super().__init__(timeout=60)
        self.author = author
        self.callback_confirm = callback_confirm
        self.callback_cancel = callback_cancel

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm action"""
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can confirm this action!", ephemeral=True)
            return
        
        try:
            await self.callback_confirm(interaction)
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(view=self)
            
        except Exception as e:
            logger.error(f"Confirmation error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel action"""
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can cancel this action!", ephemeral=True)
            return
        
        try:
            if self.callback_cancel:
                await self.callback_cancel(interaction)
            else:
                await interaction.response.send_message("❌ Action cancelled!", ephemeral=True)
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(view=self)
            
        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)

class VolumeView(discord.ui.View):
    """Music volume control interface"""
    
    def __init__(self, music_cog, guild_id: int, current_volume: int):
        super().__init__(timeout=300)
        self.music_cog = music_cog
        self.guild_id = guild_id
        self.current_volume = current_volume

    @discord.ui.button(label="🔇", style=discord.ButtonStyle.secondary)
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mute/unmute"""
        await self.set_volume(interaction, 0 if self.current_volume > 0 else 50)

    @discord.ui.button(label="🔉", style=discord.ButtonStyle.secondary)  
    async def volume_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decrease volume"""
        new_volume = max(0, self.current_volume - 10)
        await self.set_volume(interaction, new_volume)

    @discord.ui.button(label="🔊", style=discord.ButtonStyle.secondary)
    async def volume_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Increase volume"""
        new_volume = min(100, self.current_volume + 10)
        await self.set_volume(interaction, new_volume)

    async def set_volume(self, interaction: discord.Interaction, volume: int):
        """Set volume and update interface"""
        try:
            voice_client = self.music_cog.current_players.get(self.guild_id)
            
            if not voice_client or not voice_client.source:
                await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
                return
            
            voice_client.source.volume = volume / 100.0
            self.current_volume = volume
            
            await interaction.response.send_message(f"🔊 Volume set to {volume}%", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Volume control error: {e}")
            await interaction.response.send_message("❌ An error occurred!", ephemeral=True)
