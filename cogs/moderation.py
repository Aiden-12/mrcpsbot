import discord
from discord.ext import commands
from datetime import datetime
import config


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.infraction_db = {}  

    def log_infraction(self, member, action, reason, moderator):
        if member.id not in self.infraction_db:
            self.infraction_db[member.id] = []
        self.infraction_db[member.id].append({
            "action": action,
            "reason": reason,
            "moderator": moderator.name,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    # ====================== MODERATION ======================
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        self.log_infraction(member, "Warning", reason, ctx.author)
        await ctx.send(f"⚠️ **{member.mention}** has been warned.")
        await self.send_log(ctx.guild, "⚠️ Warning", f"**User:** {member.mention}\n**Reason:** {reason}", ctx.author)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: int = 10, *, reason="No reason provided"):
        try:
            await member.timeout(duration=duration*60, reason=reason)
            self.log_infraction(member, f"Mute ({duration}min)", reason, ctx.author)
            await ctx.send(f"🔇 **{member.mention}** has been muted for **{duration}** minutes.")
        except:
            await ctx.send("❌ Failed to mute user.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(f"🔊 **{member.mention}** has been unmuted.")
        except:
            await ctx.send("❌ Failed to unmute user.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 **{member}** has been kicked.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"⛔ **{member}** has been banned.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted **{amount}** messages.", delete_after=5)

    @commands.command()
    async def infractions(self, ctx, member: discord.Member):
        if member.id not in self.infraction_db or not self.infraction_db[member.id]:
            return await ctx.send(f"✅ **{member}** has no infractions.")
        embed = discord.Embed(title=f"📋 Infractions - {member}", color=discord.Color.red())
        for inf in self.infraction_db[member.id]:
            embed.add_field(name=f"{inf['action']} • {inf['time']}", value=f"**Reason:** {inf['reason']}", inline=False)
        await ctx.send(embed=embed)

    # ====================== UTILITY ======================
    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! `{latency}ms`")

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"👤 {member}", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.purple())
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blue())
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def roleinfo(self, ctx, *, role: discord.Role):
        embed = discord.Embed(title=f"📋 Role Info - {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def roles(self, ctx):
        guild = ctx.guild
        roles = sorted([r for r in guild.roles if r.name != "@everyone"], reverse=True)
        embed = discord.Embed(title=f"📋 Roles in {guild.name}", description=f"**Total:** {len(roles)}", color=discord.Color.blue())
        role_list = [f"`{role.name}` • **{len(role.members)}** members" for role in roles[:20]]
        embed.add_field(name="Roles", value="\n".join(role_list), inline=False)
        if len(roles) > 20:
            embed.set_footer(text=f"Showing first 20 of {len(roles)} roles")
        await ctx.send(embed=embed)

    # ====================== CHANNEL ======================
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏳ Slowmode set to **{seconds}** seconds.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel **locked**.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel **unlocked**.")

    # ====================== ADD ROLES (Paginated) ======================
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def addroles(self, ctx, member: discord.Member):
        """Add multiple roles with pagination"""
        if member.bot:
            return await ctx.send("❌ Cannot add roles to bots.")

        assignable_roles = [
            role for role in sorted(ctx.guild.roles, reverse=True)
            if role < ctx.guild.me.top_role and role.name != "@everyone"
        ]

        if not assignable_roles:
            return await ctx.send("❌ No roles available to assign.")

        view = PaginatedRoleView(member, assignable_roles)
        embed = discord.Embed(
            title="🎭 Add Roles to Member",
            description=f"**Member:** {member.mention}\n**Total Roles:** {len(assignable_roles)}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=view)


# ====================== PAGINATED VIEW ======================
class PaginatedRoleView(discord.ui.View):
    def __init__(self, member: discord.Member, roles: list, page: int = 0):
        super().__init__(timeout=300)
        self.member = member
        self.roles = roles
        self.page = page
        self.per_page = 25
        self.update_select()

    def update_select(self):
        self.clear_items()
        start = self.page * self.per_page
        end = start + self.per_page
        current_roles = self.roles[start:end]

        select = discord.ui.Select(
            placeholder=f"Page {self.page + 1} - Select roles",
            min_values=1,
            max_values=len(current_roles),
            options=[
                discord.SelectOption(
                    label=role.name[:100],
                    value=str(role.id),
                    description=f"{len(role.members)} members"
                ) for role in current_roles
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

        # Navigation
        self.add_item(discord.ui.Button(label="◀ Previous", style=discord.ButtonStyle.gray, disabled=self.page == 0))
        self.children[-1].callback = self.previous_page

        self.add_item(discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.gray, disabled=end >= len(self.roles)))
        self.children[-1].callback = self.next_page

    async def select_callback(self, interaction: discord.Interaction):
        selected = [int(rid) for rid in interaction.data["values"]]
        added = []
        for rid in selected:
            role = interaction.guild.get_role(rid)
            if role:
                try:
                    await self.member.add_roles(role)
                    added.append(role.name)
                except:
                    pass

        await interaction.response.send_message(
            f"✅ Added **{len(added)}** roles to {self.member.mention}:\n• " + "\n• ".join(added),
            ephemeral=False
        )

    async def previous_page(self, interaction: discord.Interaction):
        self.page -= 1
        self.update_select()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.page += 1
        self.update_select()
        await interaction.response.edit_message(view=self)

    # ====================== HELPER ======================
    async def send_log(self, guild, title, description, moderator):
        if not config.LOG_CHANNEL_ID:
            return
        log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=discord.Color.orange(), timestamp=datetime.now())
            embed.add_field(name="Moderator", value=moderator.mention)
            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))