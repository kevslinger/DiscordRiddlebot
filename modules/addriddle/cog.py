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

        embed = discord.Embed(title=f"Add a Riddle!",
                              url="https://docs.google.com/forms/d/1-5h97ZZj_6btKZXrrf7t58mPVXVJ48IW5xo69psB1kg",
                              color=utils.EMBED_COLOR)
        embed.add_field(name="How to add", value=f"A worthy riddle, you wish to add?\nGo to " +
                        "[this form](https://docs.google.com/forms/d/1-5h97ZZj_6btKZXrrf7t58mPVXVJ48IW5xo69psB1kg)," +
                        " now don't be sad.")
        await ctx.send(embed=embed)
        #await ctx.send("A worthy riddle, you wish to add?\n" + \
        #               "Go to this form, now don't be sad.\n" + \
        #               "https://docs.google.com/forms/d/1-5h97ZZj_6btKZXrrf7t58mPVXVJ48IW5xo69psB1kg")

def setup(bot):
    bot.add_cog(AddRiddleCog(bot))
