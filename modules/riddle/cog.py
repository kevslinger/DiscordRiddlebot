import os
import random
import json
from dotenv.main import load_dotenv
import discord
from discord.ext import commands
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
import modules.riddle.utils as utils

load_dotenv()

JSON_PARAMS = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri",
               "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]


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

        #######
        # Google Sheets Authentication and Initialization
        #######

        # Scope of what we can do in google drive
        scopes = ['https://www.googleapis.com/auth/spreadsheets']

        sheet_key = os.getenv('SHEET_KEY').replace('\'', '')

        # Write the credentials file if we don't have it
        if not os.path.exists('client_secret.json'):
            json_creds = dict()
            for param in JSON_PARAMS:
                json_creds[param] = os.getenv(param).replace('\"', '').replace('\\n', '\n')
            with open('client_secret.json', 'w') as f:
                json.dump(json_creds, f)
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(sheet_key).worksheet("Riddles")
        # TODO: Use Pandas Dataframe to store riddles?
        self.riddles = sheet.get_all_values()[1:]
        
        bot.loop.create_task(self.reload(bot, sheet_key, client))
        
    # Reload the Google sheet every 10 minutes so we can dynamically add
    # Without needing to restart the bot
    async def reload(self, bot, sheet_key, client):
        await bot.wait_until_ready()
        while True:
            await asyncio.sleep(600) # 10 Minutes
            sheet = client.open_by_key(sheet_key).sheet1
            self.riddles = sheet.get_all_values()[1:]
            print("Reloaded riddle sheet")
            
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

        if self.current_riddle is not None:
            embed = utils.create_riddle_embed(self.current_riddle_id, self.current_riddle, len(self.current_riddle_hints))
            embed.set_author(name="Current Riddle", icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)
            #await ctx.send(f"The current riddle is: {self.current_riddle}.\nWant a new one? " + \
            #               f"Force me to give you a new riddle with ?forceriddle")
            return 
        # TODO: get specific riddle from riddle IDif len()
        riddle_row_num = random.randint(0, len(self.riddles)-1)

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
        embed = utils.create_riddle_embed(self.current_riddle_id, self.current_riddle, len(self.current_riddle_hints))

        embed.set_author(name="New Riddle!", icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

        # Send the hint out. Good luck, users!
        #await ctx.send(f"Riddle #{self.current_riddle_id}: {self.current_riddle}\nUse ?answer to make a guess. " + \
        #               f"Remember to Spoiler Text your answers!")

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
            embed = discord.Embed(title=f"Hint Requested by {ctx.message.author}", color=utils.EMBED_COLOR)
            embed.add_field(name="Riddle", value=f"{self.current_riddle}", inline=False)
            # Increment total number of hints asked for this riddle
            self.current_given_hints += 1
            # If there are no hints
            if len(self.current_riddle_hints) == 0:
                embed.add_field(name=f"No Hints", value="Sorry, there are no hints for this riddle!", inline=False)
                #await ctx.send(embed=embed)
            # If the number of hints is more than the number of hints we have
            # Iterate over the entire list and then indicate there are no more hints left
            elif self.current_given_hints >= len(self.current_riddle_hints):
                for hint_idx, hint in enumerate(self.current_riddle_hints):
                    embed.add_field(name=f"Hint #{hint_idx+1}", value=f"|| {self.current_riddle_hints[hint_idx]} ||",
                                    inline=False)
                embed.add_field(name=f"Out of Hints", value="There are no more hints for this riddle!", inline=False)
                #await ctx.send(embed=embed)
            # If we there are more hints left
            else:
                for hint_idx, hint in enumerate(self.current_riddle_hints[:self.current_given_hints]):
                    embed.add_field(name=f"Hint {hint_idx + 1}", value=f"|| {hint} ||", inline=False)
                embed.add_field(name=f"Hints Left", value=f"There are " +
                            f"{len(self.current_riddle_hints) - self.current_given_hints} hints left for this riddle!",
                                inline=False)
                #await ctx.send(embed=embed)
        else:
            embed = utils.create_empty_embed()
            #await ctx.send(embed=embed)

        embed.set_author(name="Hint!", icon_url=ctx.message.author.avatar_url)
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
            print(ctx.message.content)
            if ctx.message.content == '?answer':
                embed = utils.create_answer_command_embed()
                await ctx.send(embed=embed)
                #await ctx.send("Usage: ?answer ||your answer||")
                return
            # People will spoiler their message with ||
            user_answer = ctx.message.content.lower().replace('?answer ', '').replace('|', '').strip()
            # some answers are answer1, answer2 and others are answer1,answer2
            # TODO: better way to do this?
            if user_answer in [correct_answer.lower() for correct_answer in self.current_riddle_possible_answers.split(', ')] or\
               user_answer in [correct_answer.lower() for correct_answer in self.current_riddle_possible_answers.split(',')]:
                embed = discord.Embed(title="Correct Answer!", color=utils.EMBED_COLOR)
                embed.add_field(name="Riddle", value=f"{self.current_riddle}", inline=False)
                if len(self.current_riddle_possible_answers) > 1:
                    possible_answers = " I would have accepted any of || [" + \
                                       ", ".join(self.current_riddle_possible_answers.split(",")) + "] ||"
                else:
                    possible_answers = ""
                embed.add_field(name="Answer", value=f"Congrats {ctx.message.author.mention}! You are correct.{possible_answers}",
                                inline=False)
                embed.set_author(name="Correct Answer!", icon_url=ctx.message.author.avatar_url)

                await ctx.send(embed=embed, reference=ctx.message, mention_author=True)
                #await ctx.send(f"Congrats {ctx.message.author.mention}! You are correct. All acceptable answers were  " +
                #               f"||{'[ ' + ', '.join(self.current_riddle_possible_answers.split(',')) + ' ]'}|| ",
                #               reference=ctx.message, mention_author=True)
            else:
                if len(self.current_riddle_hints) > 1:
                    embed = discord.Embed(title="Incorrect Answer!", color=utils.EMBED_COLOR)
                    embed.add_field(name="Riddle", value=f"{self.current_riddle}", inline=False)
                    embed.add_field(name="Answer",
                                    value=f"Sorry {ctx.message.author.mention}! You are incorrect. Can I tempt you " +
                                          f"in taking a ?hint ? If you'd like to give up, use ?showanswer",
                                    inline=False)
                    embed.set_author(name="Incorrect Answer", icon_url=ctx.message.author.avatar_url)
                    await ctx.send(embed=embed, reference=ctx.message, mention_author=True)
                    #await ctx.send(f"You're wrong {ctx.message.author.mention}. Can I tempt you in taking a ?hint? " + \
                    #               "If you'd like to give up, use ?showanswer", reference=ctx.message, mention_author=True)
                else:
                    embed = discord.Embed(title="Incorrect Answer!", color=utils.EMBED_COLOR)
                    embed.add_field(name="Riddle", value=f"{self.current_riddle}", inline=False)
                    embed.add_field(name="Answer",
                                    value=f"Sorry {ctx.message.author.mention}! You are incorrect. There are no hints" +
                                          " for this riddle. If you'd like to give up, use ?showanswer",
                                    inline=False)
                    embed.set_author(name="Incorrect Answer", icon_url=ctx.message.author.avatar_url)
                    await ctx.send(embed=embed, reference=ctx.message, mention_author=True)
                    #await ctx.send(f"You're wrong {ctx.message.author.mention}. There are no hints for this riddle, but" + \
                    #               f" if you'd like to give up, use ?showanswer", reference=ctx.message, mention_author=True)
        else:
            embed = utils.create_empty_embed()
            #embed.set_author(name="No Riddle", icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)
            #await ctx.send("No current riddle. Use ?riddle to receive a riddle")
                
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
            output_msg = f"Giving up already? The answer is: ||{self.current_riddle_possible_answers.split(',')[0]}||\n"
            #if len(self.current_riddle_possible_answers.split(',')) > 1:
            #    output_msg += f"I would have accepted any of " + \
            #        f"|| {'[ ' + ', '.join(self.current_riddle_possible_answers.split(',')) + ' ]'} ||" + \
            #        f"as a correct answer\n"
            #output_msg += "Thanks for playing! Use ?riddle to get a new riddle."
            embed = discord.Embed(title="Answer!", color=utils.EMBED_COLOR)
            embed.add_field(name="Riddle", value=f"{self.current_riddle}", inline=False)
            for hint_idx, hint in enumerate(self.current_riddle_hints):
                embed.add_field(name=f"Hint #{hint_idx + 1}", value=f"|| {self.current_riddle_hints[hint_idx]} ||",
                                inline=False)
            if len(self.current_riddle_possible_answers.split(',')) > 1:
                embed.add_field(name="Answer", value="I would have accepted any of " +
                            f"|| {'[ ' + ', '.join(self.current_riddle_possible_answers.split(',')) + ' ]'} ||",
                            inline=False)
            else:
                embed.add_field(name="Answer", value=f"The answer is || {self.current_riddle_possible_answers[0]} ||",
                                inline=False)
            await ctx.send(output_msg)
            self.reset_riddle()
        else:
            embed = utils.create_empty_embed()
            await ctx.send(embed=embed)
            await ctx.send("No current riddle. Use ?riddle to receive a riddle")

    # Function to clean the bot's riddle so it can start a new one.
    def reset_riddle(self):
        self.current_riddle = None
        self.current_riddle_possible_answers = None
        self.current_riddle_id = None
        self.current_riddle_hints = None
        self.current_given_hints = 0


def setup(bot):
    bot.add_cog(RiddleCog(bot))
