from discord.ext import commands


class AddRiddleCog(commands.Cog):
    def __init__(self, bot):
        # Bot and riddle initializations
        self.bot = bot

    @commands.command(name='addriddle')
    async def addriddle(self, ctx):
        '''
        Suggest a riddle to the bot!
        '''
        # Log command to console
        print("Received !addriddle")
        
        await ctx.send("A worthy riddle, you wish to add?\n" + \
                       "Ping kevslinger, he won't be mad.")

def setup(bot):
    bot.add_cog(AddRiddleCog(bot))
