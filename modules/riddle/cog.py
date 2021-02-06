import random
from dotenv.main import load_dotenv
import discord
from discord.ext import commands
import asyncio
import os
import modules.riddle.utils as utils

load_dotenv()


# RIDDLE_ROLE_ID = int(os.getenv("RIDDLE_ROLE_ID")) #TODO: create riddle role?
class RiddleCog(commands.Cog):
    def __init__(self, bot):
        # Bot and riddle initializations
        self.bot = bot
        self.current_riddle = None
        self.current_riddle_possible_answers = None
        self.current_riddle_id = None
        self.current_riddle_hints = None
        self.current_given_hints = 0

        # Google Sheets Authentication and Initialization
        client = utils.create_gspread_client()

        sheet_key = os.getenv('SHEET_KEY').replace('\'', '')
        sheet = client.open_by_key(sheet_key).worksheet("Riddles")
        # TODO: Use Pandas Dataframe to store riddles?
        self.riddles = sheet.get_all_values()[1:]
        
        bot.loop.create_task(self.reload(bot, sheet_key, client))
            
    # When we have an active riddle, using ?riddle will not change the riddle
    # Instead, someone will need to use ?forceriddle to get a new one
    @commands.command(name='forceriddle', aliases=['force'])
    async def forceriddle(self, ctx):
        """
        Reset the current riddle and give a new one
        Usage: ?forceriddle
        """
        # log command in console
        print("Received ?forceriddle")

        self.reset_riddle()
        await self.riddle(ctx)

    # Command to give the user a riddle.
    # If there is already an active riddle, the user will be shown that
    # a new riddle will not be created if an active one exists.
    @commands.command(name='riddle', aliases=['r'])
    async def riddle(self, ctx):
        """
        Give a riddle from our Riddle Sheet
        Usage: ?riddle
        """
        # log command in console
        print("Received ?riddle")

        # If a current riddle exists, display it again. Do not create a new riddle until
        # The users have either given up (with showanswer) or force a new riddle (with forceriddle)
        if self.current_riddle is not None:
            embed = utils.create_riddle_embed(self.current_riddle_id, self.current_riddle,
                                              len(self.current_riddle_hints))
            embed.set_author(name="See Current Riddle", icon_url=ctx.message.author.avatar_url)
        else:
            self.update_riddle()
            embed = utils.create_riddle_embed(self.current_riddle_id, self.current_riddle,
                                              len(self.current_riddle_hints))
            embed.set_author(name="Requested a New Riddle!", icon_url=ctx.message.author.avatar_url)

        await ctx.send(embed=embed)

    # Command to give a hint. The hint will have spoiler text covering it.
    @commands.command(name='hint', aliases=['h'])
    async def hint(self, ctx):
        """
        Gives a hint
        Usage: ?hint
        """
        # Log command in console
        print("Received ?hint")

        if self.current_riddle is not None:
            self.current_given_hints += 1
            embed = utils.create_hint_embed(self.current_riddle_id, self.current_riddle, self.current_riddle_hints,
                                            self.current_given_hints)
        else:
            embed = utils.create_empty_embed()

        embed.set_author(name="Requested a Hint!", icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

    # Command to check the user's answer. They will be replied to telling them whether or not their
    # answer is correct. If they are incorrect, they will be asked if they want a hint or to giveup
    @commands.command(name='answer')
    async def answer(self, ctx):
        """
        Check your  answer
        Usage: ?answer ||your answer||
        """
        # log command in console
        print("Received ?answer")
        if self.current_riddle is not None:
            user_answer = ctx.message.content.replace('?answer', '').strip()
            # If the user does not include any additional arguments, then show them how
            # To properly use the ?answer command
            if user_answer == '':
                embed = utils.create_empty_answer_command_embed()

            # If the user does not spoiler text their answer, do not answer them
            elif not user_answer.startswith('||') or not user_answer.endswith('||'):
                embed = discord.Embed(title="Spoiler Text Please!", icon_url=ctx.message.author.avatar_url)
                embed.add_field(name="Hide your answer", value="I will not check your answer until you hide it in spoiler" +
                                " text! To cover your answer, surround it in \|\| (e.g. ?answer \|\| my answer \|\|)",
                                inline=False)
            else:
                embed = utils.create_answer_embed(ctx, self.current_riddle_id, self.current_riddle, self.current_riddle_hints,
                                                  self.current_riddle_possible_answers)
                embed.set_author(name="Submitted a Guess!", icon_url=ctx.message.author.avatar_url)
        else:
            embed = utils.create_empty_embed()

        await ctx.send(embed=embed, reference=ctx.message, mention_author=True)

    # Command to use when the user has given up.
    # displays the answer (in spoiler text)
    @commands.command(name='showanswer', aliases=['show', 'giveup'])
    async def showanswer(self, ctx):
        """
        Gives the correct answer when everyone has given up
        Usage: ?showanswer
        """
        # Log command in console
        print("Received ?showanswer")

        if self.current_riddle is not None:
            embed = utils.create_showanswer_embed(self.current_riddle_id, self.current_riddle,
                                                  self.current_riddle_hints, self.current_riddle_possible_answers)
            embed.set_author(name="Giving Up!", icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)
            self.reset_riddle()
        else:
            embed = utils.create_empty_embed()
            await ctx.send(embed=embed)

    # Reload the Google sheet every 10 minutes so we can dynamically add
    # Without needing to restart the bot
    async def reload(self, bot, sheet_key, client):
        await bot.wait_until_ready()
        while True:
            await asyncio.sleep(600) # 10 Minutes
            sheet = client.open_by_key(sheet_key).sheet1
            self.riddles = sheet.get_all_values()[1:]
            print("Reloaded riddle sheet")

    # Function to clean the bot's riddle so it can start a new one.
    def reset_riddle(self):
        self.current_riddle = None
        self.current_riddle_possible_answers = None
        self.current_riddle_id = None
        self.current_riddle_hints = None
        self.current_given_hints = 0

    def update_riddle(self):
        """
        Randomly selects a riddle from our list of riddles
        Then updates the bot's fields for the new riddle
        """
        # TODO: Allow people to request certain riddles?
        riddle_row_num = random.randint(0, len(self.riddles) - 1)

        # Get riddle from sheet
        riddle_row = self.riddles[riddle_row_num]
        self.current_riddle_id = riddle_row[0]
        self.current_riddle = riddle_row[1]
        self.current_riddle_possible_answers = riddle_row[2]

        # Add all the available hints
        self.current_riddle_hints = []
        for hint_idx in range(3, len(riddle_row)):
            if riddle_row[hint_idx] is None or riddle_row[hint_idx] == '':
                continue
            self.current_riddle_hints.append(riddle_row[hint_idx])


def setup(bot):
    bot.add_cog(RiddleCog(bot))
