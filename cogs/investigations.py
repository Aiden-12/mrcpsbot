import discord
from discord.ext import commands
import config
from datetime import datetime
import json
import os

class Investigations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.PSD_ROLE_ID = 1498441157150249059
        self.cases_file = "data/psd_cases.json"
        self.cases = self.load_cases()

    def load_cases(self):
        if os.path.exists(self.cases_file):
            try:
                with open(self.cases_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_cases(self):
        os.makedirs(os.path.dirname(self.cases_file), exist_ok=True)
        with open(self.cases_file, "w") as f:
            json.dump(self.cases, f, indent=4)

    def has_psd_role(self, member: discord.Member) -> bool:
        return any(role.id == self.PSD_ROLE_ID for role in member.roles)

    def get_next_case_id(self):
        if not self.cases:
            return "PSD-0001"
        numbers = [int(case.split("-")[1]) for case in self.cases.keys() if case.startswith("PSD-")]
        return f"PSD-{max(numbers) + 1:04d}" if numbers else "PSD-0001"

    # ==================== PSD CASE COMMAND ====================
    @commands.command(name="psdcase", aliases=["case", "invest", "psd"])
    async def psd_investigation_case(self, ctx, *, details: str = "No details provided."):
        if not self.has_psd_role(ctx.author):
            await ctx.send("❌ **Access Denied.** Only PSD team members can use this command.")
            return

        case_id = self.get_next_case_id()
        log_channel = ctx.guild.get_channel(config.PSD_LOG_CHANNEL_ID)
        if not log_channel:
            await ctx.send("❌ PSD Log channel not found!")
            return

        embed = discord.Embed(
            title="🔍 PSD Investigation Case",
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="**Case ID**", value=f"`{case_id}`", inline=True)
        embed.add_field(name="**Investigator**", value=ctx.author.mention, inline=True)
        embed.add_field(name="**Status**", value="🟡 **Open**", inline=True)
        embed.add_field(name="**Opened On**", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=False)
        embed.add_field(name="**Incident Details**", value=details[:1000], inline=False)
        embed.add_field(
            name="**Required Evidence**",
            value="• Full transcript of what was said\n"
                  "• Video/Audio clip of the incident (if available)\n"
                  "• Any other relevant evidence",
            inline=False
        )
        embed.set_footer(text=f"Logged by {ctx.author} • ID: {ctx.author.id}")

        try:
            log_message = await log_channel.send(embed=embed)
            
            thread = await log_message.create_thread(
                name=f"Case {case_id} - Discussion & Evidence",
                auto_archive_duration=4320,
                reason="PSD Investigation Thread"
            )
            
            await thread.send(
                f"**{ctx.author.mention}** started this case.\n\n"
                "**Please include in this thread:**\n"
                "• Transcript of dialogue\n"
                "• Video/Audio clip\n"
                "• Any screenshots or additional evidence\n"
                "• Your findings and conclusion"
            )

            await log_message.add_reaction("🟢")
            await log_message.add_reaction("🔴")
            await log_message.add_reaction("🔄")

            self.cases[case_id] = {
                "message_id": log_message.id,
                "thread_id": thread.id,
                "channel_id": log_channel.id,
                "investigator": ctx.author.id,
                "details": details,
                "status": "Open",
                "opened_at": datetime.utcnow().isoformat()
            }
            self.save_cases()

            await ctx.send(f"✅ **Case `{case_id}`** created successfully! Thread opened.")

        except Exception:
            await ctx.send("❌ Failed to create case.")

    # ==================== PROFESSIONAL !SAY COMMAND ====================
    @commands.command(name="say")
    async def say(self, ctx, *, message: str):
        """Send a professional PSD announcement / message"""
        if not self.has_psd_role(ctx.author):
            await ctx.send("❌ **Access Denied.** Only PSD team members can use this command.")
            return

        if not message:
            await ctx.send("❌ Please provide a message.")
            return

        embed = discord.Embed(
            description=message,
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name=f"PSD Official Statement",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        embed.set_footer(text=f"Posted by {ctx.author} • PSD Division")

        try:
            await ctx.message.delete()  # Clean command usage
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Missing permissions to send message or delete command.")
        except Exception:
            await ctx.send("❌ Failed to send message.")

    # ==================== OTHER COMMANDS ====================
    @commands.command(name="psdcases")
    async def list_psd_cases(self, ctx):
        if not self.has_psd_role(ctx.author):
            await ctx.send("❌ Access Denied.")
            return

        active = [cid for cid, data in self.cases.items() if data.get("status") == "Open"]
        
        if not active:
            await ctx.send("📋 No active PSD cases.")
            return

        embed = discord.Embed(title="📋 Active PSD Cases", color=discord.Color.blue())
        for case_id in active[-10:]:
            data = self.cases[case_id]
            embed.add_field(
                name=case_id,
                value=f"**Status:** {data.get('status')}\n**Opened:** {data.get('opened_at', 'N/A')[:10]}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        message = reaction.message
        if not message.embeds or "PSD Investigation Case" not in message.embeds[0].title:
            return

        for case_id, data in self.cases.items():
            if data.get("message_id") == message.id:
                emoji = str(reaction.emoji)
                if emoji == "🟢":
                    new_status = "Closed"
                    color = discord.Color.green()
                elif emoji == "🔴":
                    new_status = "Cancelled"
                    color = discord.Color.red()
                elif emoji == "🔄":
                    new_status = "In Progress"
                    color = discord.Color.gold()
                else:
                    return

                embed = message.embeds[0]
                embed.color = color
                for field in embed.fields:
                    if field.name == "**Status**":
                        field.value = f"{emoji} **{new_status}**"

                await message.edit(embed=embed)
                self.cases[case_id]["status"] = new_status
                self.save_cases()

                await message.channel.send(f"✅ Case `{case_id}` updated to **{new_status}**", delete_after=10)
                break

async def setup(bot):
    await bot.add_cog(Investigations(bot))