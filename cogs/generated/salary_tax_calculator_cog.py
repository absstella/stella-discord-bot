import discord
from discord.ext import commands
import json
import os

class SalaryTaxCalculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tax_brackets = self.load_tax_brackets()

    def load_tax_brackets(self):
        """Loads tax brackets from a JSON file."""
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        tax_brackets_file = os.path.join(data_dir, "tax_brackets.json")
        try:
            with open(tax_brackets_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Provide default tax brackets if the file doesn't exist.
            # You should replace these with actual tax rates.
            default_brackets = [
                {"min": 0, "max": 10000, "rate": 0.10},
                {"min": 10001, "max": 40000, "rate": 0.20},
                {"min": 40001, "max": 100000, "rate": 0.30},
                {"min": 100001, "max": float('inf'), "rate": 0.40}
            ]
            with open(tax_brackets_file, "w") as f:
                json.dump(default_brackets, f, indent=4)
            return default_brackets
        except json.JSONDecodeError:
            print("Error decoding tax_brackets.json.  Check the file for errors.")
            return [] # Or raise an exception.  This will depend on error handling policy.


    def calculate_tax(self, salary):
        """Calculates income tax based on the salary and tax brackets."""
        tax = 0
        for bracket in self.tax_brackets:
            if salary > bracket["min"]:
                taxable_income = min(salary, bracket["max"]) - bracket["min"]
                tax += taxable_income * bracket["rate"]
        return tax

    @commands.slash_command(name="tax", description="Calculates income tax based on the provided gross annual salary.")
    async def tax_command(self, ctx, gross_salary: discord.Option(int, "The gross annual salary."),
                           mention_role: discord.Option(discord.Role, "The role to mention", required=False) = None,
                           mention_users: discord.Option(str, "User IDs to mention (comma separated)", required=False) = None):
        """Calculates and returns the income tax."""
        try:
            if gross_salary < 0:
                await ctx.respond("Gross salary cannot be negative.")
                return

            tax = self.calculate_tax(gross_salary)
            response = f"The income tax for a gross salary of ${gross_salary:,.2f} is ${tax:,.2f}."

            mentions = ""
            if mention_role:
                mentions += f"{mention_role.mention} "
            
            if mention_users:
                user_ids = mention_users.split(',')
                for user_id in user_ids:
                    try:
                        user_id = int(user_id.strip())
                        user = await self.bot.fetch_user(user_id)
                        mentions += f"{user.mention} "
                    except ValueError:
                        await ctx.respond(f"Invalid user ID: {user_id}")
                        return
                    except discord.NotFound:
                        await ctx.respond(f"User not found with ID: {user_id}")
                        return
                    except discord.HTTPException as e:
                        await ctx.respond(f"Failed to fetch user with ID: {user_id}. Error: {e}")
                        return


            if mentions:
                response = f"{mentions}\n{response}"

            await ctx.respond(response)

        except Exception as e:
            print(f"An error occurred: {e}")  # Log the error for debugging
            await ctx.respond(f"An error occurred while calculating the tax. Please check the input or contact the bot administrator.")


def setup(bot):
    bot.add_cog(SalaryTaxCalculator(bot))