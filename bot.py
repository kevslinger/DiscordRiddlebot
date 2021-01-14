import os, asyncio
from dotenv.main import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = '!'


def main():
    intents = discord.Intents.default()
    client = commands.Bot(BOT_PREFIX, intents=intents)

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    @client.event
    async def on_ready():
        for guild in client.guilds:
            print(f"{client.user.name} has connected to the following guild: {guild.name} (id: {guild.id})")

    client.loop.create_task(reload(client))
    client.run(DISCORD_TOKEN)

    
async def reload(bot):
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(600) # 10 minutes
    
        bot.reload_extension("modules.riddle.cog")
        print("Reloaded riddle sheet")

        
if __name__ == '__main__':
    main()
