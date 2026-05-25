import discord
from discord.ext import commands
import config
import traceback

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now ONLINE!")
    print(f"Connected to {len(bot.guilds)} server(s)")
    try:
        await bot.load_extension("cogs.antiraid")
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.promotions")
        await bot.load_extension("cogs.automod")
        await bot.load_extension("cogs.investigations")  # ← Added for PSD Investigation
        print("✅ All cogs loaded successfully!")
    except Exception as e:
        print("❌ Error loading cogs:")
        traceback.print_exc()

try:
    print("🔄 Starting bot...")
    bot.run(config.TOKEN)
except Exception as e:
    print("❌ CRITICAL ERROR:")
    traceback.print_exc()