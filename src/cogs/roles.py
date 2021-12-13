import json
import discord
from discord.ext import commands
from ext.config import save_config, check_config
from ext.confirmer import ConfirmerSession

bot = commands.Bot('')
pronouns_list = ['❤️ he ❤️', '🧡 him 🧡', '💛 she 💛', '💚 her 💚', '💙 they 💙',
                 '💜 them 💜', '🖤 it 🖤', '🤍 its 🤍', '🤎 any 🤎', '🏳️‍🌈ask me🏳️‍🌈']
divider_pronouns = '⚫️Pronouns:                ⁣'


class Roles(commands.Cog):

    def __init__(self, _bot):
        """Cog to manage Roles adding and removing by pressing buttons."""
        self.bot = _bot

    @commands.command(aliases=['rinit', 'initroles', 'initr'])
    async def rolesinit(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """<Channel> Setup the channel to display Role selections."""
        if len(channel) == 1:
            try:
                conf, settings = check_config('ROLES', None)
                # If there is already a channel set
                if settings.get('channelset') == 'True':
                    channelid = settings.get('init-channelid')
                    # Creating an embed, and sending the inital message, for the confirmer to work with
                    embed = discord.Embed(description=f"The role channel is already set to: \n"
                                                      f"<#{channelid}> - id: `{channelid}`\n"
                                                      f"Do you want to reinitiate the channel to a new one?")
                    message = await ctx.send(embed=embed)
                    # Starting the confirmer
                    response, message = await ConfirmerSession(page=embed).run(message=message)
                    # If the user choose to change the channel
                    if response:
                        # Setting the channel, creating the new embed,
                        # and editing the Original Message to reflect the Change
                        message = await setchannel(message=message, channel=channel)
                        embed = discord.Embed(description=f"The role channel was set to: \n"
                                                          f"<#{channel[0].id}> - id: `{channel[0].id}`")
                        await message.edit(embed=embed)
                    # If the user selected Cancel
                    else:
                        embed = discord.Embed(description=f"The role channel was not set")
                # If no channel was previously set
                else:
                    embed = discord.Embed(description=f"The role channel was set to: \n"
                                                      f"<#{channel[0].id}> - id: `{channel[0].id}`")
                    message = await ctx.send(embed=embed)
                    message = await setchannel(message=message, channel=channel)

                await message.edit(embed=embed)
            except Exception as e:
                await ctx.send('```' + str(e) + '```')
                return
        else:
            embed = discord.Embed(description=f"Wrong syntax!\n"
                                              f"```v!rolesinit <#channel>``` ")
            await ctx.send(embed=embed)

        await self.pronouns(ctx)

    @commands.Cog.listener()
    async def on_ready(self):
        """This function is called every time the bot restarts.
        If a view was already created before (with the same custom IDs for buttons)
        it will be loaded and the bot will start watching for button clicks again.
        """

        # Create something here, that searches for messages with buttons on them,
        # and get the matching views to add them to the bot!
        # might have to save role ids, for interactions in the settings.ini

        # we recreate the view as we did in the /post command
        view = discord.ui.View(timeout=None)
        # make sure to set the guild ID here to whatever server you want the buttons in
        _, settings = check_config('ROLES')
        role_ids = settings.get('roles')
        role_ids = json.loads(role_ids)
        guild = self.bot.get_guild(835033905978802216)
        for role_id in role_ids:
            role = guild.get_role(int(role_id))
            view.add_item(RoleButton(role))

        # add the view to the bot so it will watch for button interactions
        self.bot.add_view(view)

    async def pronouns(self, ctx):
        roles = await create_pronoun_roles(ctx)
        conf, settings = check_config('ROLES')
        pmessageid = settings.get('PronounsMessageID')
        if pmessageid is None:
            embed = discord.Embed(
                description='give or remove Pronouns from your profile, by clicking the Buttons below',
                title='Pronouns')
            components = []
            for r in roles:
                components.append(r)
            view = ReactView(components=components)
            roleschannelid = settings.get('init-channelid')
            channel = self.bot.get_channel(int(roleschannelid))
            message = await channel.send(embed=embed, view=view)
            conf.set('ROLES', 'PronounsMessageID', str(message.id))

        # if message.id is not None:
        #    embed = discord.Embed(title='Pronouns',
        #                          colour=Colour(0xE5E242),
        #                          description='Select your pronouns by clicking on the buttons')
        #    view = discord.ui.View(timeout=None)

        #    message = await ctx.send(view=view, embed=embed)
        #    messageid = self.message.id
        #    #conf.set('ROLES', 'PronounsMessageID', str(self.messageid))
        #    save_config(self.conf)


async def create_pronoun_roles(ctx):
    guild = ctx.guild
    roles = []
    # Create the divider beginning role
    if discord.utils.get(guild.roles, name=divider_pronouns) is None:
        await guild.create_role(name=divider_pronouns)
    # Create the Pronoun roles
    for pronoun in pronouns_list:
        if discord.utils.get(guild.roles, name=pronoun) is None:
            roles.append(await guild.create_role(name=pronoun))
        else:
            roles.append(discord.utils.get(guild.roles, name=pronoun))
    # checking for missing roles in the settings.ini
    conf = check_settings_for_roles(roles=roles)
    # save the config into settings.ini
    save_config(config=conf)
    return roles


def check_settings_for_roles(roles):
    # checking if the ids already exist in the settings.ini
    conf, settings = check_config('ROLES', None)
    # creating a list of the roleids to be added
    roleids = []
    for role in roles:
        roleids.append(str(role.id))
    # checking if any of the roleids are missing in the settings.ini
    list_of_roles = settings.get('roles')

    # Incase the role section is missing in ROLES
    if list_of_roles is None:
        roleids = list_to_json(roleids)
    # Check if anything is missing in [ROLES]:roles
    else:
        list_of_roles = json.loads(list_of_roles)
        for role in roles:
            if str(role.id) not in list_of_roles:
                list_of_roles.append(str(role.id))
        roleids = list_to_json(list_of_roles)

    # write into the config
    conf.set('ROLES', 'roles', roleids)
    return conf


def list_to_json(items):
    buffer = json.dumps(items).split(',')
    newitems = ''
    for index, item in enumerate(buffer):
        newitems += item
        if index + 1 < len(buffer):
            newitems += ',\n'
    return newitems


async def channel_set(message, channel, conf):
    embed = discord.Embed(title="Channel Confirm", colour=discord.Colour(0x269a78),
                          description="Are you sure you want to set the roles channel to:\n"
                                      "<#{}> ?".format(channel.id))
    response, message = await ConfirmerSession(page=embed).run(message=message)
    if response is True:
        conf.set('ROLES', 'Init-ChannelName', str(channel.name))
        conf.set('ROLES', 'Init-ChannelID', str(channel.id))
        conf.set('ROLES', 'channelSet', 'True')
    else:
        embed = discord.Embed(description=f"The roles channel was not set",
                              colour=discord.Colour(0xbf212f))
        await message.edit(embed=embed)
        return message, None
    return message, conf


def get_config():
    return check_config('ROLES', None)


async def setchannel(message, channel):
    conf, _ = get_config()
    embedctx, conf = await channel_set(message=message, channel=channel[0], conf=conf)
    save_config(conf)
    return embedctx


class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        """
        A button for one role. `custom_id` is needed for persistent views.
        """
        super().__init__(
            label=role.name,
            style=discord.enums.ButtonStyle.grey,
            custom_id=str(role.id),
        )

    async def callback(self, interaction: discord.Interaction):
        """This function will be called any time a user clicks on this button
        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object that was created when the user clicked on the button
        """

        # figure out who clicked the button
        user = interaction.user
        # get the role this button is for (stored in the custom ID)
        role = interaction.guild.get_role(int(self.custom_id))

        if role is None:
            # if this role doesn't exist, ignore
            # you can do some error handling here
            return

        # passed all checks
        # add the role and send a response to the uesr ephemerally (hidden to other users)
        if role not in user.roles:
            # give the user the role if they don't already have it
            await user.add_roles(discord.utils.get(interaction.guild.roles, name=divider_pronouns))
            await user.add_roles(role)
            await interaction.response.send_message(
                f"🎉 You have been given the role {role.mention}", ephemeral=True)
        else:
            # else, take the role from the user
            await user.remove_roles(role)
            await interaction.response.send_message(
                f"❌ The {role.mention} role has been taken from you", ephemeral=True)


class ReactView(discord.ui.View):

    def __init__(self, components: list):
        """ReactView init."""
        super().__init__()
        for c in components:
            self.add_item(RoleButton(c))


def setup(bot):
    bot.add_cog(Roles(bot))
