import os
import random
import json
from dotenv.main import load_dotenv
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

JSON_PARAMS = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]


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
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


        SHEET_KEY = os.getenv('SHEET_KEY').replace('\'', '')

        # Write the credentials file if we don't have it
        if not os.path.exists('client_secret.json'):
            json_creds = dict()
            for param in JSON_PARAMS:
                json_creds[param] = os.getenv(param).replace('\"', '').replace('\\n', '\n')
            with open('client_secret.json', 'w') as f:
                json.dump(json_creds, f)
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', SCOPES)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_KEY).sheet1
        self.riddles = sheet.get_all_values()[1:]
        
        bot.loop.create_task(reload(client))
        
    # Reload the Google sheet every 10 minutes so we can dynamically add
    # Without needing to restart the bot
    async def reload(self, client):
        await bot.wait_until_ready()
        while True:
            await asyncio.sleep(600) # 10 minutes
            sheet = client.open_by_key(SHEET_KEY).sheet1
            self.riddles = sheet.get_all_values()[1:]
            print("Reloaded riddle sheet")

            
    # When we have an active riddle, using !riddle will not change the riddle
    # Instead, someone will need to use !forceriddle to get a new one
    @commands.command(name='forceriddle')
    async def forceriddle(self, ctx):
        '''
        Reset the current riddle and give a new one
        Usage: !forceriddle
        '''
        # log command in console
        print("Received !forceriddle")

        self.reset_riddle()
        await self.riddle(ctx)

    # Command to give the user a riddle.
    # If there is already an active riddle, the user will be shown that
    # a new riddle will not be created if an active one exists.
    @commands.command(name='riddle')
    async def riddle(self, ctx):
        '''
        Give a riddle from our Riddle Sheet
        Usage: !riddle
        '''
        # log command in console
        print("Received !riddle")

        if self.current_riddle is not None:
            await ctx.send(f"The current riddle is: {self.current_riddle}.\nWant a new one? Force me to give you a new riddle with !forceriddle")
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
        # Send the hint out. Good luck, users!
        await ctx.send(f'Riddle #{self.current_riddle_id}: {self.current_riddle}\nUse !answer to make a guess. Remember to Spoiler Text your answers!')

    # Command to give a hint. The hint will have spoiler text covering it.
    @commands.command(name='hint')
    async def hint(self, ctx):
        '''
        Gives a hint 
        Usage: !hint
        '''
        # Log command in console
        print("Received !hint")
        
        if self.current_riddle is not None:
            if len(self.current_riddle_hints) > 0:
                self.current_given_hints += 1
                await ctx.send(f"Hint {self.current_given_hints}: ||{self.current_riddle_hints.pop(0)}||")
            elif self.current_given_hints > 0:
                await ctx.send(f"Only {self.current_given_hints} hints were available for this riddle\n" + \
                               "If you're stumped, you can use !showanswer to get the answer.")
            else:
                await ctx.send(f"No hints for this riddle.\nIf you're stumped, you can use !showanswer to get the answer.")
        else:
            await ctx.send("No current riddle. Use !riddle to receive a riddle")

    # Command to check the user's answer. They will be replied to telling them whether or not their
    # answer is correct. If they are incorrect, they will be asked if they want a hint or to giveup
    @commands.command(name='answer')
    async def answer(self, ctx):
        '''
        Check your  answer
        Usage: !answer ||your answer||
        '''
        # log command in console
        print("Received !answer")
        
        print(ctx.message.content)
        if ctx.message.content == '!answer':
            await ctx.send("Usage: !answer ||your answer||")
            return
        # People will spoiler their message with ||
        user_answer = ctx.message.content.lower().replace('!answer ', '').replace('|', '').strip()
        # some answers are answer1, answer2 and others are answer1,answer2
        if user_answer in [correct_answer.lower() for correct_answer in self.current_riddle_possible_answers.split(', ')] or user_answer in [correct_answer.lower() for correct_answer in self.current_riddle_possible_answers.split(',')]:
            await ctx.send(f"Congrats {ctx.message.author.mention}! You are correct. All acceptable answers were  ||{'[ ' + ', '.join(self.current_riddle_possible_answers.split(',')) + ' ]'}|| ", reference=ctx.message, mention_author=True)
        else:
            if len(self.current_riddle_hints) > 1:
                await ctx.send(f"You're wrong {ctx.message.author.mention}. Can I tempt you in taking a !hint? If you'd like to give up, use !showanswer", reference=ctx.message, mention_author=True)
            else:      
                await ctx.send(f"You're wrong {ctx.message.author.mention}. There are no hints for this riddle, but if you'd like to give up, use !showanswer", reference=ctx.message, mention_author=True)
                
    # Command to use when the user has given up.
    # displays the answer (in spoiler text)
    @commands.command(name='showanswer')
    async def showanswer(self, ctx):
        '''
        Gives the correct answer when the users have given up
        Usage: !showanswer
        '''
        # Log command in console
        print("Received !showanswer")
        
        output_msg = f"Giving up already? The answer is: ||{self.current_riddle_possible_answers.split(',')[0]}||\n"
        if len(self.current_riddle_possible_answers.split(',')) > 1:
            output_msg += f"I would have accepted any of ||{'[ ' + ', '.join(self.current_riddle_possible_answers.split(',')) + ' ]'}|| as a correct answer\n"
        output_msg += "Thanks for playing! Use !riddle to get a new riddle."
        await ctx.send(output_msg)
        self.reset_riddle()

    # Function to clean the bot's riddle so it can start a new one.
    def reset_riddle(self):
        self.current_riddle = None
        self.current_riddle_answer = None
        self.current_riddle_id = None
        self.current_riddle_hints = None
        self.current_given_hints = 0
        
def setup(bot):
    bot.add_cog(RiddleCog(bot))
