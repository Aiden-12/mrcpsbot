import discord
from discord.ext import commands
import config

class Promotions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def promote(self, ctx, *, message: str):
        """Post a promotion in the promotions channel"""
        # Try to find promotions channel, fallback to current channel
        promo_channel = discord.utils.get(ctx.guild.text_channels, name="promotions")
        if not promo_channel:
            promo_channel = ctx.channel

        embed = discord.Embed(
            title="🎉 Server Promotion",
            description=message,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Promoted by {ctx.author}")
        embed.timestamp = discord.utils.utcnow()

        await promo_channel.send(embed=embed)
        await ctx.send("✅ Promotion posted successfully!")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def boost(self, ctx, member: discord.Member = None):
        """Thank a server booster"""
        target = member or ctx.author
        
        embed = discord.Embed(
            title="💎 Thank You for Boosting!",
            description=f"{target.mention} just boosted the server!\nThank you so much for your support! ❤️",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Promotions(bot))