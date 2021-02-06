import discord


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
    embed = discord.Embed(title=f"Riddle #{riddle_id}", color=EMBED_COLOR)
    embed.add_field(name="Riddle", value=f"{riddle}", inline=False)
    embed.add_field(name="Answering", value="Use ?answer to make a guess. Remember to Spoiler Text your answers!",
                    inline=False)
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


def create_answer_command_embed():
    """
    Function to create an embed to display command usage.
    :param command: (str) The command used
    :return embeD: (discord.Embed) The embed we create
    """
    embed = discord.Embed(title=f"Answer", color=EMBED_COLOR)
    embed.add_field(name=f"Answer Usage", value="?answer ||your_answer||", inline=False)
    return embed



