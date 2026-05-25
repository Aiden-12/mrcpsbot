import discord
from discord.ext import commands
import config
from collections import deque
import time

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_log = deque()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        now = time.time()
        
        # Clean old joins
        while self.join_log and self.join_log[0] < now - config.JOIN_TIME_WINDOW:
            self.join_log.popleft()

        self.join_log.append(now)

        # Anti-Raid Detection
        if len(self.join_log) >= config.JOIN_RATE_LIMIT:
            await self.activate_lockdown(member.guild)

        # New account check
        if (now - member.created_at.timestamp()) < config.NEW_ACCOUNT_AGE:
            try:
                await member.kick(reason="New account - Anti-Raid")
                await self.log_action(member.guild, "New Account Kicked", member)
            except:
                pass

    async def activate_lockdown(self, guild: discord.Guild):
        log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send("🚨 **RAID DETECTED!** Activating lockdown...")

        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.default_role)
            if perms.send_messages:
                try:
                    await channel.edit(slowmode_delay=30)
                except:
                    pass

    async def log_action(self, guild, action, member):
        log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="Anti-Raid Action",
                description=f"**Action:** {action}\n**User:** {member.mention}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))