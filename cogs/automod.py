import discord
from discord.ext import commands
import re
import config
import asyncio
from datetime import datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation_cog = None

        # ==================== CONFIGURABLE SETTINGS ====================
        self.bad_words = [
            "nigger", "nigga", "faggot", "fag", "cunt", "whore",
            "slut", "tranny", "chink"
        ]

        self.spam_threshold = 5          # Messages in 10 seconds
        self.caps_ratio = 0.75           # 75%+ caps
        self.max_mentions = 4
        self.max_links = 3

        # Anti-Spam tracking
        self.message_log = {}  # user_id: [timestamps]

    async def get_moderation_cog(self):
        if not self.moderation_cog:
            self.moderation_cog = self.bot.get_cog("Moderation")
        return self.moderation_cog

    # ====================== MAIN MESSAGE CHECK ======================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Ignore commands
        if message.content.startswith(config.PREFIX):
            return

        content = message.content.lower()
        mod_cog = await self.get_moderation_cog()

        # === 1. Bad Words Filter ===
        for word in self.bad_words:
            if word in content or any(word in w for w in message.content.lower().split()):
                await self.punish(message, "Profanity", mod_cog, delete=True)
                return

        


        # === 4. Discord Invite Links ===
        if re.search(r"(discord\.(gg|com/invite|app\.com/invite))/[a-zA-Z0-9-]+", message.content):
            await self.punish(message, "Unauthorized Invite", mod_cog, delete=True)
            return

        # === 5. Link Spam ===
        links = re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", message.content)
        if len(links) > self.max_links:
            await self.punish(message, "Link Spam", mod_cog, delete=True)
            return

        # === 6. Spam Detection (Message Flood) ===
        await self.check_spam(message, mod_cog)

    async def check_spam(self, message, mod_cog):
        user_id = message.author.id
        now = datetime.now().timestamp()

        if user_id not in self.message_log:
            self.message_log[user_id] = []

        # Add current message timestamp
        self.message_log[user_id].append(now)

        # Remove old messages (older than 10 seconds)
        self.message_log[user_id] = [t for t in self.message_log[user_id] if now - t < 10]

        if len(self.message_log[user_id]) >= self.spam_threshold:
            await self.punish(message, "Spam / Flooding", mod_cog, delete=True)
            # Clear log after punishment
            self.message_log[user_id] = []

    async def punish(self, message, reason, mod_cog, delete=True):
        try:
            if delete:
                await message.delete()

            # Log infraction
            if mod_cog:
                mod_cog.log_infraction(
                    message.author,
                    "AutoMod",
                    reason,
                    self.bot.user
                )

            # Send warning
            warning = await message.channel.send(
                f"⚠️ {message.author.mention} **AutoMod Triggered**\n"
                f"**Reason:** `{reason}`"
            )

            await asyncio.sleep(6)
            await warning.delete()

            # Log to log channel
            log_channel = message.guild.get_channel(config.LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title="🛡️ AutoMod Action",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="User", value=message.author.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=True)
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                await log_channel.send(embed=embed)

        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"AutoMod Error: {e}")

    # ====================== COMMANDS ======================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addbadword(self, ctx, *, word: str):
        """Add a bad word to the filter"""
        word = word.lower().strip()
        if word not in self.bad_words:
            self.bad_words.append(word)
            await ctx.send(f"✅ Added `{word}` to swear words list.")
        else:
            await ctx.send("❌ Word already in list.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def badwords(self, ctx):
        """Show all bad words"""
        embed = discord.Embed(title="🚫 AutoMod Swear Words", color=discord.Color.red())
        embed.description = ", ".join(self.bad_words) if self.bad_words else "None"
        embed.set_footer(text=f"Total: {len(self.bad_words)} words")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def automodsettings(self, ctx):
        """Show current AutoMod settings"""
        embed = discord.Embed(title="⚙️ AutoMod Settings", color=discord.Color.blue())
        embed.add_field(name="Spam Threshold", value=f"{self.spam_threshold} messages / 10s", inline=False)
        embed.add_field(name="Caps Ratio", value=f"{self.caps_ratio*100}%", inline=False)
        embed.add_field(name="Max Mentions", value=self.max_mentions, inline=False)
        embed.add_field(name="Max Links", value=self.max_links, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))