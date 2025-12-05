import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/minecraft"
        self.servers_file = os.path.join(self.data_dir, "servers.json")
        self.coords_file = os.path.join(self.data_dir, "coords.json")
        self.coords_file = os.path.join(self.data_dir, "coords.json")
        self.trades_file = os.path.join(self.data_dir, "trades.json")
        self.monitor_file = os.path.join(self.data_dir, "monitor.json")
        
        self._ensure_data_files()
        self.server_monitor_loop.start()

    def cog_unload(self):
        self.server_monitor_loop.cancel()
        
    def _ensure_data_files(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        for file_path in [self.servers_file, self.coords_file, self.trades_file, self.monitor_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)

    def _load_json(self, file_path) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}

    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")

    # --- Server Management ---

    mc_group = app_commands.Group(name="mc", description="Minecraft utilities")
    admin_group = app_commands.Group(name="admin", description="Minecraft admin commands", parent=mc_group)

    @admin_group.command(name="add_server", description="[Admin] サーバーの通称とIPを登録します")
    @app_commands.describe(alias="通称 (例: AbsCL)", ip="サーバーIP")
    @app_commands.default_permissions(administrator=True)
    async def add_server(self, interaction: discord.Interaction, alias: str, ip: str):
        data = self._load_json(self.servers_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data:
            data[guild_id] = {}
            
        data[guild_id][alias] = ip
        self._save_json(self.servers_file, data)
        
        await interaction.response.send_message(f"✅ サーバーを登録しました: **{alias}** -> `{ip}`")

    @admin_group.command(name="remove_server", description="[Admin] サーバー登録を削除します")
    @app_commands.describe(alias="通称")
    @app_commands.default_permissions(administrator=True)
    async def remove_server(self, interaction: discord.Interaction, alias: str):
        data = self._load_json(self.servers_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id in data and alias in data[guild_id]:
            del data[guild_id][alias]
            self._save_json(self.servers_file, data)
            await interaction.response.send_message(f"✅ サーバー登録を削除しました: **{alias}**")
        else:
            await interaction.response.send_message(f"❌ その通称のサーバーは見つかりませんでした。", ephemeral=True)

    @admin_group.command(name="list_servers", description="[Admin] 登録済みサーバー一覧を表示します")
    @app_commands.default_permissions(administrator=True)
    async def list_servers(self, interaction: discord.Interaction):
        data = self._load_json(self.servers_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data or not data[guild_id]:
            await interaction.response.send_message("📭 登録されているサーバーはありません。", ephemeral=True)
            return
            
        embed = discord.Embed(title="📋 登録済みサーバー一覧", color=discord.Color.green())
        for alias, ip in data[guild_id].items():
            embed.add_field(name=alias, value=f"`{ip}`", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @mc_group.command(name="status", description="サーバーのステータスを確認します")
    @app_commands.describe(target="通称またはIPアドレス")
    async def server_status(self, interaction: discord.Interaction, target: str):
        await interaction.response.defer()
        
        # Check if target is an alias
        data = self._load_json(self.servers_file)
        guild_id = str(interaction.guild_id)
        ip = target
        
        if guild_id in data and target in data[guild_id]:
            ip = data[guild_id][target]
            
        # Fetch status using mcsrvstat.us API
        api_url = f"https://api.mcsrvstat.us/2/{ip}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    await interaction.followup.send(f"❌ ステータスの取得に失敗しました (HTTP {response.status})")
                    return
                
                status_data = await response.json()
                
        if not status_data.get("online"):
            await interaction.followup.send(f"🔴 **{target}** ({ip}) はオフラインです。")
            return
            
        # Online
        embed = discord.Embed(title=f"🟢 {target} Status", color=discord.Color.green())
        embed.description = f"**IP**: `{ip}`\n**Version**: {status_data.get('version')}"
        
        players = status_data.get("players", {})
        online_count = players.get("online", 0)
        max_count = players.get("max", 0)
        
        embed.add_field(name="👥 Players", value=f"{online_count} / {max_count}", inline=True)
        
        # Motd
        motd = status_data.get("motd", {}).get("clean", [])
        if motd:
            embed.add_field(name="💬 MOTD", value="\n".join(motd), inline=False)
            
        # Player list (if available)
        player_list = players.get("list", [])
        if player_list:
            embed.add_field(name="📝 Online Users", value=", ".join(player_list), inline=False)
            
        # Icon
        if "icon" in status_data:
            # The icon is base64, discord embed doesn't support base64 directly easily without attachment
            # For simplicity, we skip icon or use a default thumbnail
            pass
            
        await interaction.followup.send(embed=embed)

    # --- Coordinate System ---

    coords_group = app_commands.Group(name="coords", description="Manage coordinates", parent=mc_group)

    @coords_group.command(name="add", description="座標を保存します")
    @app_commands.describe(name="場所の名前", x="X座標", y="Y座標", z="Z座標", dimension="ディメンション (overworld/nether/end)")
    @app_commands.choices(dimension=[
        app_commands.Choice(name="オーバーワールド", value="Overworld"),
        app_commands.Choice(name="ネザー", value="Nether"),
        app_commands.Choice(name="エンド", value="End")
    ])
    async def add_coords(self, interaction: discord.Interaction, name: str, x: int, y: int, z: int, dimension: str = "Overworld"):
        data = self._load_json(self.coords_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data:
            data[guild_id] = {}
            
        data[guild_id][name] = {
            "x": x, "y": y, "z": z,
            "dim": dimension,
            "author": interaction.user.display_name,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_json(self.coords_file, data)
        await interaction.response.send_message(f"📍 座標を保存しました: **{name}** ({x}, {y}, {z}) [{dimension}]")

    @coords_group.command(name="list", description="保存された座標一覧を表示します")
    async def list_coords(self, interaction: discord.Interaction):
        data = self._load_json(self.coords_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data or not data[guild_id]:
            await interaction.response.send_message("📭 保存された座標はありません。", ephemeral=True)
            return
            
        embed = discord.Embed(title="📍 座標リスト", color=discord.Color.blue())
        
        for name, info in data[guild_id].items():
            dim_icon = "🌍" if info["dim"] == "Overworld" else "🔥" if info["dim"] == "Nether" else "🌌"
            embed.add_field(
                name=f"{dim_icon} {name}",
                value=f"`{info['x']}, {info['y']}, {info['z']}`\nBy: {info['author']}",
                inline=True
            )
            
        await interaction.response.send_message(embed=embed)

    @coords_group.command(name="delete", description="座標を削除します")
    @app_commands.describe(name="場所の名前")
    async def delete_coords(self, interaction: discord.Interaction, name: str):
        data = self._load_json(self.coords_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id in data and name in data[guild_id]:
            del data[guild_id][name]
            self._save_json(self.coords_file, data)
            await interaction.response.send_message(f"🗑️ 座標を削除しました: **{name}**")
        else:
            await interaction.response.send_message(f"❌ その名前の座標は見つかりませんでした。", ephemeral=True)

    # --- Trade System ---

    trade_group = app_commands.Group(name="trade", description="Manage trades", parent=mc_group)

    @trade_group.command(name="offer", description="トレードを募集します")
    @app_commands.describe(give_item="出すアイテム", give_count="出す数", want_item="欲しいアイテム", want_count="欲しい数")
    async def trade_offer(self, interaction: discord.Interaction, give_item: str, give_count: int, want_item: str, want_count: int):
        data = self._load_json(self.trades_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data:
            data[guild_id] = []
            
        trade_id = len(data[guild_id]) + 1
        # Ensure unique ID if deletions happened (simple approach: max + 1)
        if data[guild_id]:
            trade_id = max(t["id"] for t in data[guild_id]) + 1
            
        trade = {
            "id": trade_id,
            "author_id": interaction.user.id,
            "author_name": interaction.user.display_name,
            "give": {"item": give_item, "count": give_count},
            "want": {"item": want_item, "count": want_count},
            "created_at": datetime.now().isoformat()
        }
        
        data[guild_id].append(trade)
        self._save_json(self.trades_file, data)
        
        embed = discord.Embed(title="⚖️ 新しいトレード募集", color=discord.Color.gold())
        embed.add_field(name="出", value=f"{give_item} x{give_count}", inline=True)
        embed.add_field(name="求", value=f"{want_item} x{want_count}", inline=True)
        embed.set_footer(text=f"ID: {trade_id} | 募集者: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @trade_group.command(name="list", description="募集中トレード一覧を表示します")
    async def list_trades(self, interaction: discord.Interaction):
        data = self._load_json(self.trades_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id not in data or not data[guild_id]:
            await interaction.response.send_message("📭 現在募集中のトレードはありません。", ephemeral=True)
            return
            
        embed = discord.Embed(title="⚖️ トレード掲示板", color=discord.Color.gold())
        
        for trade in data[guild_id]:
            embed.add_field(
                name=f"ID: {trade['id']} ({trade['author_name']})",
                value=f"📤 **出**: {trade['give']['item']} x{trade['give']['count']}\n📥 **求**: {trade['want']['item']} x{trade['want']['count']}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

    @trade_group.command(name="accept", description="トレードを成立させます（募集者に通知します）")
    @app_commands.describe(trade_id="トレードID")
    async def accept_trade(self, interaction: discord.Interaction, trade_id: int):
        data = self._load_json(self.trades_file)
        guild_id = str(interaction.guild_id)
        
        target_trade = None
        if guild_id in data:
            for trade in data[guild_id]:
                if trade["id"] == trade_id:
                    target_trade = trade
                    break
        
        if not target_trade:
            await interaction.response.send_message("❌ そのIDのトレードは見つかりませんでした。", ephemeral=True)
            return
            
        # Notify owner
        owner_id = target_trade["author_id"]
        owner = interaction.guild.get_member(owner_id)
        
        msg = f"✅ **トレード成立！**\n{interaction.user.mention} があなたのトレード(ID: {trade_id})に応じました！\n連絡を取り合って交換してください。"
        
        if owner:
            try:
                await owner.send(msg)
            except:
                pass # DM closed
        
        # Remove trade
        data[guild_id].remove(target_trade)
        self._save_json(self.trades_file, data)
        
        await interaction.response.send_message(f"{interaction.user.mention} がトレード(ID: {trade_id})を成立させました！募集者に通知を送りました。")

    @trade_group.command(name="delete", description="自分のトレード募集を取り消します")
    @app_commands.describe(trade_id="トレードID")
    async def delete_trade(self, interaction: discord.Interaction, trade_id: int):
        data = self._load_json(self.trades_file)
        guild_id = str(interaction.guild_id)
        
        target_trade = None
        if guild_id in data:
            for trade in data[guild_id]:
                if trade["id"] == trade_id:
                    target_trade = trade
                    break
        
        if not target_trade:
            await interaction.response.send_message("❌ そのIDのトレードは見つかりませんでした。", ephemeral=True)
            return
            
        if target_trade["author_id"] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 他人のトレードは削除できません。", ephemeral=True)
            return
            
        data[guild_id].remove(target_trade)
        self._save_json(self.trades_file, data)
        
        await interaction.response.send_message(f"🗑️ トレード(ID: {trade_id})を取り消しました。")

    # --- Server Monitor ---

    monitor_group = app_commands.Group(name="monitor", description="Server auto-monitoring", parent=mc_group)

    @monitor_group.command(name="set", description="サーバー監視パネルを作成します")
    @app_commands.describe(target="監視するサーバー(通称/IP)", channel="表示するチャンネル(指定なしで現在地)")
    @app_commands.default_permissions(administrator=True)
    async def monitor_set(self, interaction: discord.Interaction, target: str, channel: discord.TextChannel = None):
        await interaction.response.defer()
        
        if not channel:
            channel = interaction.channel
            
        # Resolve IP
        data = self._load_json(self.servers_file)
        guild_id = str(interaction.guild_id)
        ip = target
        alias = target
        
        if guild_id in data and target in data[guild_id]:
            ip = data[guild_id][target]
        else:
            # If target is raw IP, use it as alias too if not found
            pass

        # Create initial message
        embed = discord.Embed(title=f"📡 {alias} Server Monitor", description="Initializing...", color=discord.Color.orange())
        embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            msg = await channel.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ メッセージの送信に失敗しました: {e}")
            return

        # Save config
        monitor_data = self._load_json(self.monitor_file)
        monitor_data[guild_id] = {
            "channel_id": channel.id,
            "message_id": msg.id,
            "ip": ip,
            "alias": alias
        }
        self._save_json(self.monitor_file, monitor_data)
        
        await interaction.followup.send(f"✅ **{alias}** の監視パネルを {channel.mention} に作成しました。5分ごとに更新されます。")
        # Trigger immediate update
        await self.update_server_status(guild_id, monitor_data[guild_id])

    @monitor_group.command(name="stop", description="サーバー監視を停止します")
    @app_commands.default_permissions(administrator=True)
    async def monitor_stop(self, interaction: discord.Interaction):
        monitor_data = self._load_json(self.monitor_file)
        guild_id = str(interaction.guild_id)
        
        if guild_id in monitor_data:
            # Try to delete the message
            try:
                info = monitor_data[guild_id]
                channel = self.bot.get_channel(info["channel_id"])
                if channel:
                    msg = await channel.fetch_message(info["message_id"])
                    await msg.delete()
            except:
                pass
            
            del monitor_data[guild_id]
            self._save_json(self.monitor_file, monitor_data)
            await interaction.response.send_message("✅ サーバー監視を停止しました。")
        else:
            await interaction.response.send_message("❌ 監視設定が見つかりませんでした。", ephemeral=True)

    @tasks.loop(minutes=5)
    async def server_monitor_loop(self):
        monitor_data = self._load_json(self.monitor_file)
        for guild_id, info in list(monitor_data.items()):
            await self.update_server_status(guild_id, info)

    @server_monitor_loop.before_loop
    async def before_monitor_loop(self):
        await self.bot.wait_until_ready()

    async def update_server_status(self, guild_id, info):
        channel_id = info["channel_id"]
        message_id = info["message_id"]
        ip = info["ip"]
        alias = info["alias"]
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return # Channel might be deleted or bot not in guild
            
        try:
            msg = await channel.fetch_message(message_id)
        except:
            # Message deleted, remove config
            monitor_data = self._load_json(self.monitor_file)
            if guild_id in monitor_data:
                del monitor_data[guild_id]
                self._save_json(self.monitor_file, monitor_data)
            return

        # Fetch status
        api_url = f"https://api.mcsrvstat.us/2/{ip}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        status_data = None
                    else:
                        status_data = await response.json()
        except:
            status_data = None

        if not status_data or not status_data.get("online"):
            # Offline
            embed = discord.Embed(title=f"🔴 {alias} Server Monitor", color=discord.Color.red())
            embed.description = f"**Status**: Offline\n**IP**: `{ip}`"
            embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        else:
            # Online
            embed = discord.Embed(title=f"🟢 {alias} Server Monitor", color=discord.Color.green())
            embed.description = f"**Status**: Online\n**IP**: `{ip}`\n**Version**: {status_data.get('version')}"
            
            players = status_data.get("players", {})
            online_count = players.get("online", 0)
            max_count = players.get("max", 0)
            
            embed.add_field(name="👥 Players", value=f"{online_count} / {max_count}", inline=True)
            
            motd = status_data.get("motd", {}).get("clean", [])
            if motd:
                embed.add_field(name="💬 MOTD", value="\n".join(motd), inline=False)
                
            player_list = players.get("list", [])
            if player_list:
                embed.add_field(name="📝 Online Users", value=", ".join(player_list), inline=False)
                
            embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

        try:
            await msg.edit(embed=embed)
        except:
            pass

async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
