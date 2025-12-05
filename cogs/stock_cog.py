import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = os.path.join("data", "stock_market.json")
        self.stock_data = self.load_data()
        self.update_stock_prices.start()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load stock data: {e}")
        return {"stocks": {}, "portfolios": {}, "last_update": None}

    def save_data(self):
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.stock_data, f, indent=4, ensure_ascii=False)

    def calculate_price(self, member):
        # Base price
        price = 100.0
        
        # Random fluctuation (market noise)
        price += random.uniform(-5, 5)
        
        # Activity bonus (mock logic for now, ideally would track real activity)
        # In a real implementation, we'd hook into on_message to track activity counts
        # For now, we'll use a randomized "momentum" based on status
        if str(member.status) == "online":
            price += random.uniform(0, 10)
        elif str(member.status) == "idle":
            price += random.uniform(-2, 5)
        elif str(member.status) == "dnd":
            price += random.uniform(5, 15) # Busy people are high value?
        else:
            price += random.uniform(-5, 0)
            
        # Cap limits
        return max(1.0, round(price, 2))

    @tasks.loop(minutes=10)
    async def update_stock_prices(self):
        """Update stock prices for all members"""
        logger.info("Updating stock prices...")
        
        for guild in self.bot.guilds:
            # Find target role (Absmember or similar)
            target_role = None
            for role in guild.roles:
                if "absmember" in role.name.lower() or "abscl" in role.name.lower():
                    target_role = role
                    break
            
            for member in guild.members:
                if member.bot:
                    continue
                
                # If target role exists, only track members with that role
                if target_role and target_role not in member.roles:
                    continue
                
                user_id = str(member.id)
                current_price = self.stock_data["stocks"].get(user_id, {}).get("price", 100.0)
                
                # Calculate new price based on "activity" (simulated for now)
                change = random.uniform(-10, 10)
                if str(member.status) == "online":
                    change += 5
                
                new_price = max(1.0, current_price + change)
                
                self.stock_data["stocks"][user_id] = {
                    "name": member.display_name,
                    "price": round(new_price, 2),
                    "previous_price": current_price
                }
        
        self.stock_data["last_update"] = datetime.now().isoformat()
        self.save_data()

    @update_stock_prices.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_group(name="stock", description="メンバー株取引システム")
    async def stock(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドを指定してください: market, buy, sell, portfolio")

    @stock.command(name="market", description="現在の株価一覧を表示します")
    async def market(self, ctx):
        """Show current stock market"""
        if not self.stock_data["stocks"]:
            await ctx.send("📉 データ収集中です。しばらくお待ちください。")
            # Force update for first run
            await self.update_stock_prices()
            
        embed = discord.Embed(title="📈 メンバー株価市場", color=discord.Color.blue())
        
        # Sort by price descending
        sorted_stocks = sorted(
            self.stock_data["stocks"].items(), 
            key=lambda x: x[1]['price'], 
            reverse=True
        )[:10] # Top 10
        
        description = ""
        for i, (uid, data) in enumerate(sorted_stocks, 1):
            price = data['price']
            prev = data.get('previous_price', price)
            diff = price - prev
            
            emoji = "🔺" if diff > 0 else "🔻" if diff < 0 else "➡️"
            diff_str = f"{diff:+.2f}"
            
            description += f"{i}. **{data['name']}**: {price:.2f} P ({emoji} {diff_str})\n"
            
        embed.description = description or "データなし"
        embed.set_footer(text="価格は10分ごとに変動します")
        await ctx.send(embed=embed)

    @stock.command(name="buy", description="メンバーの株を購入します")
    @app_commands.describe(user="購入するメンバー", amount="購入数")
    async def buy(self, ctx, user: discord.Member, amount: int):
        """Buy stocks"""
        if amount <= 0:
            await ctx.send("❌ 1株以上指定してください。")
            return
            
        user_id = str(user.id)
        buyer_id = str(ctx.author.id)
        
        if user_id not in self.stock_data["stocks"]:
            # Initialize if not exists
            self.stock_data["stocks"][user_id] = {
                "name": user.display_name,
                "price": 100.0,
                "previous_price": 100.0
            }
            
        price = self.stock_data["stocks"][user_id]["price"]
        cost = price * amount
        
        # Check balance (using a mock balance for now, or integrate with EconomyCog if exists)
        # For this prototype, everyone has infinite money or starts with 10000
        portfolio = self.stock_data["portfolios"].get(buyer_id, {"balance": 10000.0, "stocks": {}})
        
        if portfolio["balance"] < cost:
            await ctx.send(f"❌ 資金不足です！ (残高: {portfolio['balance']:.2f} P, 必要: {cost:.2f} P)")
            return
            
        # Execute trade
        portfolio["balance"] -= cost
        current_qty = portfolio["stocks"].get(user_id, 0)
        portfolio["stocks"][user_id] = current_qty + amount
        
        self.stock_data["portfolios"][buyer_id] = portfolio
        self.save_data()
        
        await ctx.send(f"✅ **{user.display_name}** の株を {amount}株 購入しました！ (総額: {cost:.2f} P)")

    @stock.command(name="sell", description="メンバーの株を売却します")
    @app_commands.describe(user="売却するメンバー", amount="売却数")
    async def sell(self, ctx, user: discord.Member, amount: int):
        """Sell stocks"""
        if amount <= 0:
            await ctx.send("❌ 1株以上指定してください。")
            return
            
        user_id = str(user.id)
        buyer_id = str(ctx.author.id)
        
        portfolio = self.stock_data["portfolios"].get(buyer_id, {"balance": 10000.0, "stocks": {}})
        current_qty = portfolio["stocks"].get(user_id, 0)
        
        if current_qty < amount:
            await ctx.send(f"❌ 保有株数が足りません！ (保有: {current_qty}株)")
            return
            
        price = self.stock_data["stocks"].get(user_id, {}).get("price", 100.0)
        earnings = price * amount
        
        # Execute trade
        portfolio["balance"] += earnings
        portfolio["stocks"][user_id] = current_qty - amount
        
        # Clean up if 0
        if portfolio["stocks"][user_id] == 0:
            del portfolio["stocks"][user_id]
            
        self.stock_data["portfolios"][buyer_id] = portfolio
        self.save_data()
        
        await ctx.send(f"✅ **{user.display_name}** の株を {amount}株 売却しました！ (利益: {earnings:.2f} P)")

    @stock.command(name="portfolio", description="自分の保有株と資産を表示します")
    async def portfolio(self, ctx):
        """Show portfolio"""
        buyer_id = str(ctx.author.id)
        portfolio = self.stock_data["portfolios"].get(buyer_id, {"balance": 10000.0, "stocks": {}})
        
        embed = discord.Embed(title=f"💼 {ctx.author.display_name}のポートフォリオ", color=discord.Color.green())
        embed.add_field(name="現金残高", value=f"{portfolio['balance']:.2f} P", inline=False)
        
        total_assets = portfolio['balance']
        stock_list = ""
        
        for uid, qty in portfolio["stocks"].items():
            stock_info = self.stock_data["stocks"].get(uid, {"name": "Unknown", "price": 0})
            value = stock_info["price"] * qty
            total_assets += value
            stock_list += f"• **{stock_info['name']}**: {qty}株 (価値: {value:.2f} P)\n"
            
        if stock_list:
            embed.add_field(name="保有株式", value=stock_list, inline=False)
        else:
            embed.add_field(name="保有株式", value="なし", inline=False)
            
        embed.add_field(name="総資産", value=f"💰 {total_assets:.2f} P", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StockCog(bot))
