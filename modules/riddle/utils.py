import discord
import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

EMBED_COLOR = 0xd4e4ff

# TODO: Generalize this to "create_embed" function? Could be useful util
def create_riddle_embed(riddle_id, riddle, num_hints):
    """
    Function to create the riddle embed
    :param riddle_id: (int) The id # of the current riddle
    :param riddle: (str) The riddle string
    :param num_hints: (int) The number of hints for this riddle

    :return embed: (discord.Embed) The embed we create for the riddle
    """
    embed = discord.Embed(color=EMBED_COLOR)
    embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)
    embed.add_field(name="Answering", value="Use ?answer to make a guess. Remember to Spoiler Text your answers!",
                    inline=False)
    if num_hints == 0:
        embed.add_field(name="Hint", value="Sorry, there are no hints for this riddle!", inline=False)
    else:
        embed.add_field(name="Hint", value=f"If you're stuck, try ?hint to get a hint.\n" +
                                       f"There are {num_hints} hints for this riddle", inline=False)
    embed.add_field(name="New Riddle", value="Want a new riddle? Force me to give you one with ?forceriddle",
                    inline=False)
    return embed


def create_empty_embed():
    """
    Function to create an embed to say there is no riddle

    :return embed: (discord.Embed) The embed we create
    """
    embed = discord.Embed(title="No Riddle!", color=EMBED_COLOR)
    embed.add_field(name="No Current Riddle", value="Use ?riddle to get a riddle, or ?help to see options.",
                    inline=False)
    return embed


def create_empty_answer_command_embed():
    """
    Function to create an embed to display command usage.
    :return embed: (discord.Embed) The embed we create
    """
    embed = discord.Embed(color=EMBED_COLOR)
    embed.add_field(name="Answer Usage", value="?answer ||your answer||", inline=False)
    embed.add_field(name="Giving Up?", value="To give up and see the answer, use ?showanswer", inline=False)
    return embed


def create_hint_embed(riddle_id, riddle, hints, num_given_hints):
    embed = discord.Embed(color=EMBED_COLOR)
    embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)

    # If there are no hints
    if len(hints) == 0:
        embed.add_field(name=f"No Hints", value="Sorry, there are no hints for this riddle!", inline=False)
    # If the number of hints is more than the number of hints we have
    # Iterate over the entire list and then indicate there are no more hints left
    elif num_given_hints >= len(hints):
        for hint_idx, hint in enumerate(hints):
            embed.add_field(name=f"Hint #{hint_idx + 1}", value=f"|| {hints[hint_idx]} ||",
                            inline=False)
        embed.add_field(name=f"Out of Hints", value="There are no more hints for this riddle!", inline=False)
    # If we there are more hints left
    else:
        for hint_idx, hint in enumerate(hints[:num_given_hints]):
            embed.add_field(name=f"Hint #{hint_idx + 1}", value=f"|| {hint} ||", inline=False)
        embed.add_field(name=f"Hints Left", value=f"There are " +
                                                  f"{len(hints) - num_given_hints} hints left for this riddle!",
                        inline=False)

    return embed


def create_answer_embed(ctx, riddle_id, riddle, hints, answers):
    # Do not accept an answer that isn't spoilered!
    # People will spoiler their message with ||
    user_answer = ctx.message.content.lower().replace('?answer ', '').replace('|', '').strip()
    # some answers are answer1, answer2 and others are answer1,answer2
    # TODO: better way to do this?
    if user_answer in [correct_answer.lower() for correct_answer in answers.split(', ')] or \
            user_answer in [correct_answer.lower() for correct_answer in
                            answers.split(',')]:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)
        if len(answers) > 1:
            possible_answers = " I would have accepted any of || [" + \
                               ", ".join(answers.split(",")) + "] ||"
        else:
            possible_answers = ""
        embed.add_field(name="Correct Answer",
                        value=f"Congrats {ctx.message.author.mention}! You are correct.{possible_answers}",
                        inline=False)
    else:
        if len(hints) > 1:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)
            embed.add_field(name="Incorrect Answer!",
                            value=f"Sorry {ctx.message.author.mention}! You are incorrect. Can I tempt you " +
                                  f"in taking a ?hint ? If you'd like to give up, use ?showanswer",
                            inline=False)
        else:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)
            embed.add_field(name="Incorrect Answer!",
                            value=f"Sorry {ctx.message.author.mention}! You are incorrect. There are no hints" +
                                  " for this riddle. If you'd like to give up, use ?showanswer",
                            inline=False)
    return embed


def create_showanswer_embed(riddle_id, riddle, hints, answers):
    embed = discord.Embed(color=EMBED_COLOR)
    embed.add_field(name=f"Riddle #{riddle_id}", value=f"{riddle}", inline=False)
    for hint_idx, hint in enumerate(hints):
        embed.add_field(name=f"Hint #{hint_idx + 1}", value=f"|| {hints[hint_idx]} ||",
                        inline=False)
    if len(answers.split(',')) > 1:
        embed.add_field(name="Answer", value="I would have accepted any of " +
                                             f"|| {'[ ' + ', '.join(answers.split(',')) + ' ]'} ||",
                        inline=False)
    else:
        embed.add_field(name="Answer", value=f"The answer is || {answers[0]} ||",
                        inline=False)
    embed.add_field(name="Thanks for Playing!", value="To get a new riddle, use ?riddle")
    return embed


JSON_PARAMS = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri",
               "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]


def create_gspread_client():
    # Scope of what we can do in google drive
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    # Write the credentials file if we don't have it
    if not os.path.exists('client_secret.json'):
        json_creds = dict()
        for param in JSON_PARAMS:
            json_creds[param] = os.getenv(param).replace('\"', '').replace('\\n', '\n')
        with open('client_secret.json', 'w') as f:
            json.dump(json_creds, f)
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scopes)
    return gspread.authorize(creds)


