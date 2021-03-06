import discord
import configparser
import pytz

from discord.ext import commands
from distutils.util import strtobool
from datetime import datetime

channelId = None
logEvents = []

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot('', intents=intents)


class ModLog(commands.Cog):

    def __init__(self, _bot):
        self.bot = _bot

    @commands.command(aliases=['log'], no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx, *args):
        """Admin Only!!, setup logging channel."""

        config = check_config()

        if len(args) >= 1:

            if args[0] == "setchannel":
                if len(args) == 2:
                    _id = args[1].replace("<", "").replace("#", "").replace(">", "")
                    if _id.isnumeric():

                        if self.bot.get_channel(int(_id)) is not None:
                            config.set('MODLOG', 'id', str(id))
                            save_config(config)

                            embed = discord.Embed(description=f"The log channel was set to {args[1]}",
                                                  colour=discord.Colour(0x37b326))
                            return await ctx.send(embed=embed)

                    embed = discord.Embed(description=f"Please enter a valid channel!",
                                          colour=discord.Colour(0xbf212f))
                    return await ctx.send(embed=embed)
        return

    # LISTENERS #
    @commands.Cog.listener()
    async def on_member_join(self, member):

        embed = discord.Embed(title="Member Joined", colour=discord.Colour(0xd03b9))

        embed.set_thumbnail(url=member.avatar)
        embed.set_footer(text=f"User ID: {member.id} | Joined at:")

        embed.add_field(name=f"<@{member.id}>", value=f"{member.name}{member.discriminator}")
        embed.add_field(name="Account Age", value=member.joined_at)

        return await send_embed_to_log(self, event="on_member_join", embed=embed, timestamp=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name="Member Left", icon_url=member.avatar_url)
        embed.description = f"{member.mention} | {member.name}#{member.discriminator}"
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=f"User ID: {member.id}")

        return await send_embed_to_log(self, event="on_member_leave", embed=embed, timestamp=True)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        e = discord.Embed(color=discord.Color.blue())
        e.set_author(name="Member Updated", icon_url=after.avatar_url)
        e.set_footer(text=f"User ID: {after.id}")
        r_before = [role.id for role in before.roles]
        r_after = [role.id for role in after.roles]
        if before.nick != after.nick:
            e.description = f"{after.mention} Nickname changed."
            e.add_field(name="Before:", value=f"{before.nick}", inline=False)
            e.add_field(name="After:", value=f"{after.nick}", inline=False)
            return await send_embed_to_log(self, event="on_member_nickname_change", embed=e, timestamp=True)
        if before.roles != after.roles:
            r = list(set(r_before) ^ set(r_after))
            if r not in r_before and r not in r_after:
                if len(before.roles) < len(after.roles):
                    e.description = f"**{after.mention} was given the <@&{r[0]}> role.**"
                elif len(before.roles) > len(after.roles):
                    e.description = f"**{after.mention} was removed from the <@&{r[0]}> role.**"
                return await send_embed_to_log(self, event="on_role_give", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            e = discord.Embed(color=discord.Color.red())
            e.set_author(name=f'{message.author}', icon_url=message.author.avatar_url)
            e.description = f"**Message sent by {message.author.mention} deleted in {message.channel.mention}.**"
            if len(message.content) > 1024:
                content = message.content[:1021] + "..."
                e.add_field(name="Message Content:", value=f"{content}")
            else:
                e.add_field(name="Message Content:", value=f"{message.content} \u200b")
            if len(message.attachments) > 0:
                e.add_field(name="Number of attachments:", value=f"{len(message.attachments)}", inline=False)
            e.set_footer(text=f"User ID: {message.author.id} | Message ID: {message.id}")

            return await send_embed_to_log(self, event="on_message_delete", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        guild = messages[0].channel.guild
        e = discord.Embed(color=discord.Color.red())
        e.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon.url is not None else '')
        e.description = f"**Bulk messages deleted in {messages[0].channel.mention}, {len(messages)} messages deleted.**"
        return await send_embed_to_log(self, event="on_message_bulk_delete", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        e = discord.Embed(color=discord.Color.blue())
        e.set_author(name=f"{before.author}", icon_url=f"{before.author.avatar_url}")
        e.set_footer(text=f"User ID: {after.author.id}")
        if before.content != after.content:
            e.description = f"**Message edited in {before.channel.mention}. " \
                            f"[Jump to message]" \
                            f"(https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}/)**"
            if len(before.content) > 1024:
                content = before.content[:1021] + "..."
                e.add_field(name="Before:", value=f"{content}")
            else:
                e.add_field(name="Before:", value=f"{before.content} \u200b")
            if len(after.content) > 1024:
                content = after.content[:1021] + "..."
                e.add_field(name="After:", value=f"{content}")
            else:
                e.add_field(name="After:", value=f"{after.content} \u200b")
            return await send_embed_to_log(self, event="on_message_edit", embed=e, timestamp=True)
        else:
            if before.pinned and not after.pinned:
                e.description = f"**Message unpinned in {after.channel.mention}. " \
                                f"[Jump to message]" \
                                f"(https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}/)**"
                return await send_embed_to_log(self, event="on_message_pin", embed=e, timestamp=True)
            elif not before.pinned and after.pinned:
                e.description = f"**Message was pinned in {after.channel.mention}. " \
                                f"[Jump to message]" \
                                f"(https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}/)**"
                return await send_embed_to_log(self, event="on_message_unpin", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        e = discord.Embed(color=discord.Color.blue())
        e.set_author(name="Server Updated", icon_url=after.icon.url if after.icon is not None else '')
        if before.name != after.name or before.region != after.region or \
                before.afk_timeout != after.afk_timeout or before.afk_channel != after.afk_channel or \
                before.icon != after.icon or before.owner_id != after.owner_id or before.banner != after.banner:
            if before.name != after.name:
                e.add_field(name="Server Name Changed:", value=f"**Before:** {before.name}\n**After:** {after.name}",
                            inline=False)
            if before.region != after.region:
                e.add_field(name="Server Region Changed:",
                            value=f"**Before:** {before.region}\n**After:** {after.region}", inline=False)
            if before.afk_timeout != after.afk_timeout:
                e.add_field(name="Server AFK-Timeout Channel Changed:",
                            value=f"**Before:** {before.afk_timeout}\n**After:** {after.afk_timeout}", inline=False)
            if before.afk_channel != after.afk_channel:
                e.add_field(name="Server AFK-Timeout Channel Changed:",
                            value=f"**Before:** {before.afk_channel}\n**After:** {after.afk_channel}", inline=False)
            if before.icon != after.icon:
                if before.icon is not None and after.icon is not None:
                    e.add_field(name="Server Icon Changed:",
                                value=f"**Before:** {before.icon.url}\n**After:** {after.icon.url}", inline=False)
                if before.icon is None:
                    e.add_field(name="Server Icon Changed:",
                                value=f"**Before:** -not set-\n**After:** {after.icon.url}", inline=False)
                if after.icon is None:
                    e.add_field(name="Server Icon Changed:",
                                value=f"**Before:** {before.icon.url}\n**After:** -removed-", inline=False)

            if before.owner_id != after.owner_id:
                e.add_field(name="Server Owner Changed:",
                            value=f"**Before:** <@{before.owner_id}>\n**After:** <@{after.owner_id}>", inline=False)
            if before.banner != after.banner:
                e.add_field(name="Server Banner Changed:",
                            value=f"**Before:** {before.banner.url}\n**After:** {after.banner.url}", inline=False)
            return await send_embed_to_log(self, event="on_guild_update", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        e = discord.Embed(color=discord.Color.green())
        e.set_author(name="Role Created", icon_url=role.guild.icon.url if role.guild.icon is not None else '')
        e.description = f"{role.mention} | {role.name}"
        e.set_footer(text=f"Role ID: {role.id}")

        return await send_embed_to_log(self, event="on_role_delete", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        e = discord.Embed(color=discord.Color.red())
        e.set_author(name="Role Deleted", icon_url=role.guild.icon.url if role.guild.icon is not None else '')
        e.description = f"@{role.name}"

        return await send_embed_to_log(self, event="on_role_delete", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        e = discord.Embed(color=discord.Color.blue())
        e.set_author(name="Role Updated", icon_url=after.guild.icon.url if after.guild.icon is not None else '')
        if before.name != after.name or before.color != after.color:
            if before.name != after.name:
                e.add_field(name="Role's name changed:", value=f"**Before:** {before.name}\n**After:** {after.name}",
                            inline=False)
            if before.color != after.color:
                e.add_field(name="Role's color changed:",
                            value=f"**Before:** {before.color.value}\n**After:** {after.color.value}", inline=False)

            return await send_embed_to_log(self, event="on_role_update", embed=e, timestamp=True)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):

        embed = discord.Embed(colour=discord.Color.blue(),
                              description=f"**Invite created in {invite.channel.mention} "
                                          f"with an ID of **{invite.id}**. [Invite link]({invite.url})**")

        embed.set_author(name="Invite Created", icon_url=invite.guild.icon.url if invite.guild.icon is not None else '')

        time = invite.max_age
        inf = ""

        if time == 0:
            inf = "???"
        days = time // (24 * 3600)
        time = time % (24 * 3600)
        hours = time // 3600
        time %= 3600
        minutes = time // 60

        days = str(days) + " days" if days > 0 else ""
        hours = str(hours) + " hours" if hours > 0 else ""
        minutes = str(minutes) + " minutes" if minutes > 0 else ""

        embed.add_field(name="Created By", value=invite.inviter, inline=False)
        embed.add_field(name="Max Age", value="Expires in " + inf + days + hours + minutes + "", inline=True)
        embed.add_field(name="Max Uses", value=invite.max_uses, inline=True)
        return await send_embed_to_log(self, event="on_invite_create", embed=embed, timestamp=True)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):

        embed = discord.Embed(colour=discord.Color.blue(),
                              description=f"**Invite deleted in {invite.channel.mention} with an ID of **{invite.id}")

        embed.set_author(name="Invite Deleted", icon_url=invite.guild.icon.url if invite.guild.icon is not None else '')
        return await send_embed_to_log(self, event="on_invite_delete", embed=embed, timestamp=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        e = discord.Embed()
        e.set_author(name=f"{member}", icon_url=member.avatar_url)
        if before.channel != after.channel:
            if before.channel is None and after.channel is not None:
                e.description = f"{member.mention} **joined voice channel {after.channel.mention}**"
                e.colour = discord.Color.green()
                e.set_footer(text=f"Channel ID: {after.channel.id}")
                return await send_embed_to_log(self, event="on_member_join_vc", embed=e, timestamp=True)
            elif before.channel is not None and after.channel is None:
                e.description = f"{member.mention} **left voice channel {before.channel.mention}**"
                e.colour = discord.Color.red()
                e.set_footer(text=f"Channel ID: {before.channel.id}")
                return await send_embed_to_log(self, event="on_member_leave_vc", embed=e, timestamp=True)
            elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                e.description = f"{member.mention} **moved from {before.channel.mention} to {after.channel.mention}**"
                e.colour = discord.Color.blue()
                e.set_footer(text=f"Channel ID before: {before.channel.id} | Channel ID after: {after.channel.id}")
                return await send_embed_to_log(self, event="on_member_moved_vc", embed=e, timestamp=True)
        else:
            e.set_footer(text=f"Channel ID: {after.channel.id}")
            if before.mute != after.mute:
                if after.mute:
                    e.description = f"{member.mention} **was server muted in {after.channel.mention}**"
                    e.colour = discord.Color.red()
                else:
                    e.description = f"{member.mention} **was un-server muted in {after.channel.mention}**"
                    e.colour = discord.Color.green()
                return await send_embed_to_log(self, event="on_member_mute_vc", embed=e, timestamp=True)
            elif before.deaf != after.deaf:
                if after.deaf:
                    e.description = f"{member.mention} **was server deafened in {after.channel.mention}**"
                    e.colour = discord.Color.red()
                else:
                    e.description = f"{member.mention} **was un-server deafened in {after.channel.mention}**"
                    e.colour = discord.Color.green()
                return await send_embed_to_log(self, event="on_member_deaf_vc", embed=e, timestamp=True)


async def send_embed_to_log(self, event, embed, timestamp=False):
    config = check_config()
    _channelId = config.get('MODLOG', 'id')
    if _channelId is not None:
        if timestamp:
            embed.timestamp = datetime.now(pytz.timezone('US/Pacific'))

        event = config.get('MODLOG', event)
        event = strtobool(event)
        if event == 1:
            logchannel = self.bot.get_channel(int(_channelId))
            return await logchannel.send(embed=embed)


def save_config(config):
    with open('settings.ini', 'w+') as configfile:
        config.write(configfile)
        return True


def check_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # checking for existing config
    if config.has_section('MODLOG'):
        config.get('MODLOG', 'ID')
        config.get('MODLOG', 'on_member_join')
        config.get('MODLOG', 'on_member_nickname_change')
        config.get('MODLOG', 'on_member_join_vc')
        config.get('MODLOG', 'on_member_moved_vc')
        config.get('MODLOG', 'on_member_mute_vc')
        config.get('MODLOG', 'on_member_deaf_vc')
        config.get('MODLOG', 'on_invite_create')
        config.get('MODLOG', 'on_member_leave')
        config.get('MODLOG', 'on_member_ban')
        config.get('MODLOG', 'on_member_kick')
        config.get('MODLOG', 'on_message_edit')
        config.get('MODLOG', 'on_message_delete')
        config.get('MODLOG', 'on_message_bulk_delete')
        config.get('MODLOG', 'on_message_pin')
        config.get('MODLOG', 'on_message_unpin')
        config.get('MODLOG', 'on_channel_create')
        config.get('MODLOG', 'on_channel_delete')
        config.get('MODLOG', 'on_role_create')
        config.get('MODLOG', 'on_role_update')
        config.get('MODLOG', 'on_role_give')
        config.get('MODLOG', 'on_role_delete')
        config.get('MODLOG', 'on_moderator_command')
        config.get('MODLOG', 'on_guild_update')
        config.get('MODLOG', 'on_invite_create')
        config.get('MODLOG', 'on_invite_delete')
    else:
        # writing default config, incase none has been found
        config['MODLOG'] = \
            {
                'ID': 'None',
                'on_member_join': 'False',
                'on_member_nickname_change': 'False',
                'on_member_join_vc': 'False',
                'on_member_moved_vc': 'False',
                'on_member_mute_vc': 'False',
                'on_member_deaf_vc': 'False',
                'on_member_leave_vc': 'False',
                'on_member_leave': 'False',
                'on_member_ban': 'False',
                'on_member_kick': 'False',
                'on_message_edit': 'False',
                'on_message_delete': 'False',
                'on_message_bulk_delete': 'False',
                'on_message_pin': 'False',
                'on_message_unpin': 'False',
                'on_channel_create': 'False',
                'on_channel_delete': 'False',
                'on_role_create': 'False',
                'on_role_update': 'False',
                'on_role_give': 'False',
                'on_role_delete': 'False',
                'on_moderator_command': 'False',
                'on_guild_update': 'False',
                'on_invite_create': 'False',
                'on_invite_delete': 'False',
            }
        try:
            with open('settings.ini', 'w+') as configfile:
                config.write(configfile)
        except Exception as e:
            print('```error writing config: ' + str(e) + ' ```')
    return config


def setup(_bot):
    bot.add_cog(ModLog(_bot))
