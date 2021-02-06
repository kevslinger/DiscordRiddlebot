import discord
from discord.ext import commands
import modules.riddle.utils as utils


class AddRiddleCog(commands.Cog):
    def __init__(self, bot):
        # Bot and riddle initializations
        self.bot = bot

    @commands.command(name='addriddle', aliases=['add'])
    async def addriddle(self, ctx):
        """
        Suggest a riddle to the bot!
        """
        # Log command to console
        print("Received !addriddle")

        embed = discord.Embed(title=f"Google Form to Submit a New Riddle!",
                              url="https://docs.google.com/forms/d/1-5h97ZZj_6btKZXrrf7t58mPVXVJ48IW5xo69psB1kg",
                              color=utils.EMBED_COLOR)
        embed.add_field(name="How to add", value=f"A worthy riddle, you wish to add? Go to " +
                        "[this form](https://docs.google.com/forms/d/1-5h97ZZj_6btKZXrrf7t58mPVXVJ48IW5xo69psB1kg)," +
                        " now don't be sad.")
        embed.set_author(name="Wants to Add a Riddle!", icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AddRiddleCog(bot))
