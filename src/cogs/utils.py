import discord
from discord.ext import commands

from ..single_guild_bot import SingleGuildBot as Bot


class Utilities(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def code(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Here is how to format Python code on Discord:",
            description="\`\`\`py\n"
            "print('Hello World!')"
            "\n\`\`\`\n"
            "```py\nprint('Hello World!')\n```",
        )
        embed.set_author(icon_url=self.bot.user.avatar_url, name="ArjanBot")
        embed.set_footer(text="These are backticks, not single quotes!")

        await ctx.send(embed=embed)
