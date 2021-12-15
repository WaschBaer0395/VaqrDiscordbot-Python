import json
import discord
import validators
from discord.ext import commands
from discord.utils import get

from ext.config import save_config, check_config
from ext.confirmer import ConfirmerSession

bot = commands.Bot('')
pronouns_list = ['❤️ he ❤️', '🧡 him 🧡', '💛 she 💛', '💚 her 💚', '💙 they 💙',
                 '💜 them 💜', '🖤 it 🖤', '🤍 its 🤍', '🤎 any 🤎', '🏳️‍🌈ask me🏳️‍🌈']
divider_pronouns = '⚫️Pronouns:                ⁣'
role_color = discord.Colour.blurple()


class Roles(commands.Cog):

    def __init__(self, _bot):
        """Cog to manage Roles adding and removing by pressing buttons."""
        self.bot = _bot

    @commands.command(aliases=['rinit', 'initroles', 'initr'])
    async def rolesinit(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """<#channel> setup role channel."""
        if len(channel) == 1:
            try:
                _, settings = check_config('ROLES', None)
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

    @commands.command(aliases=['rcreate'])
    async def reac_message_create(self, ctx, *, args):
        """<title> <text> <opt.banner url> create a react message """
        description = ''
        title = ''
        banner = None
        embeds = []

        # Split the given arguments into the pieces used to create the embeds
        # Missing an error handling incase the format for an embed is wrong!
        # ToDo: Create error handling for this method!
        args = args.split('\n')
        for idx, a in enumerate(args):
            if idx == 0:
                title = a
            elif not validators.url(a):
                description += a + '\n'
            else:
                banner = a

        # Check the settings.ini if there is already a list of Embeds in the Role channel
        _, settings = check_config('ROLES')
        channel = self.bot.get_channel(int(settings.get('init-channelid')))

        # Incase a Banner was set for the Embed message
        if banner is not None:
            bannerembed = discord.Embed(color=role_color)
            bannerembed.set_image(url=banner)
            embeds.append(bannerembed)
        # Add the message itself as an embed
        textembed = discord.Embed(title=title, color=role_color, description=description)
        embeds.append(textembed)

        message = await channel.send(embeds=embeds)
        conf, settings = check_config('ROLES')
        msettings = settings.get('messages')
        messages = []
        if msettings is None:
            messages.append(message.id)
        else:
            messages = json.loads(msettings)
            messages.append(message.id)
        conf.set('ROLES', 'messages', str(list_to_json(messages)))
        save_config(conf)

    @commands.command()
    async def add_reaction(self, ctx, role: discord.Role, *args):
        """<@role> <reactname> -> select message to add to"""
        # ToDo: add error handling incase the role does not exsist
        if len(args) == 0:
            embed = discord.Embed(color=discord.Colour.red(), description='Error, please give the Role a name!')
            view = None
        else:
            description = 'Please select a message to add the reaction to'
            items = []
            _, settings = check_config('ROLES')
            messageids = settings.get('messages')
            messageids = json.loads(messageids)
            channelid = settings.get('init-channelid')
            channel = await ctx.guild.fetch_channel(channelid)
            for messageid in messageids:
                message = await channel.fetch_message(messageid)
                for em in message.embeds:
                    if em.title is not discord.Embed.Empty:
                        d = {'title': em.title, 'id': messageid}
                        items.append(d)
            embed = discord.Embed(color=role_color, description=description)
            message = await ctx.send(embed=embed)
            view = DropdownView(options=items, channel=channel, role=role, name=args[0], ctx=ctx, message=message)
            await message.edit(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        """This function is called every time the bot restarts."""
        # If a view was already created before (with the same custom IDs for buttons)
        # it will be loaded and the bot will start watching for button clicks again.

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
        roleids.append(role.id)
    # checking if any of the roleids are missing in the settings.ini
    list_of_roles = settings.get('roles')

    # Incase the role section is missing in ROLES
    if list_of_roles is None:
        roleids = list_to_json(roleids)
    # Check if anything is missing in [ROLES]:roles
    else:
        list_of_roles = json.loads(list_of_roles)
        for role in roles:
            if role.id not in list_of_roles:
                list_of_roles.append(role.id)
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
    embed = discord.Embed(title="Channel Confirm", colour=role_color,
                          description="Are you sure you want to set the roles channel to:\n"
                                      "<#{}> ?".format(channel.id))
    response, message = await ConfirmerSession(page=embed).run(message=message)
    if response is True:
        conf.set('ROLES', 'Init-ChannelName', str(channel.name))
        conf.set('ROLES', 'Init-ChannelID', str(channel.id))
        conf.set('ROLES', 'channelSet', 'True')
    else:
        embed = discord.Embed(description=f"The roles channel was not set",
                              colour=role_color)
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
    def __init__(self, role: discord.Role, name=None):
        """A button for one role. `custom_id` is needed for persistent views."""
        if name is None:
            name = role.name
        super().__init__(
            label=name,
            style=discord.enums.ButtonStyle.grey,
            custom_id=str(role.id),
        )

    async def callback(self, interaction: discord.Interaction):
        """ Function that will be called any time a user clicks on this button."""
        # Parameters
        # ----------
        # interaction : discord.Interaction
        #    The interaction object that was created when the user clicked on the button

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

    def __init__(self, components: list, names=None):
        """Reactview init."""
        super().__init__()
        for idx, c in enumerate(components):
            self.add_item(RoleButton(c, name=names[idx]))


class AddReactionsList(discord.ui.Select):

    def __init__(self, options: list, channel, role, name, guild, message):
        # Set the options that will be presented inside the dropdown

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        _, settings = check_config('ROLES')
        messageids = settings.get('messages')
        messageids = json.loads(messageids)
        self.channel = channel
        self.role = role
        self.name = name
        self.guild = guild
        self.selection_message = message

        opt = []
        for item in options:
            opt.append(discord.SelectOption(label=item['title'], value=item['id']))

        super().__init__(
            placeholder="Select a message",
            min_values=1,
            max_values=1,
            options=opt,
        )

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        message = await self.channel.fetch_message(self.values[0])
        components = [self.role]
        edit = False
        names = [self.name]
        if len(message.components) == 0:
            view = ReactView(components, names=names)
        else:
            view = discord.ui.View.from_message(message)
            roles = []
            names = []
            for child in view.children:
                role = get(self.guild.roles, id=int(child.__getattribute__('custom_id')))
                if role.id == self.role.id:
                    edit = True
                    names.append(self.name)
                else:
                    names.append(child.__getattribute__('label'))
                roles.append(role)

            if not edit:
                roles.append(self.role)
                names.append(self.name)
            view = ReactView(roles, names=names)

        embeds = message.embeds
        conf, settings = check_config('ROLES')
        roles = settings.get('roles')
        roles = json.loads(roles)
        roles.append(self.role.id)
        roles = list_to_json(roles)
        conf.set('ROLES', 'roles', roles)
        save_config(conf)
        await message.edit(embeds=embeds, view=view)
        embed = discord.Embed(color=role_color, description='Button has been added/edited')
        await self.selection_message.edit(embed=embed, view=None)


class DropdownView(discord.ui.View):

    def __init__(self, options: list, channel, role, name, ctx, message):
        """Dropdownview init."""
        super().__init__()
        guild = ctx.guild
        self.add_item(
            item=AddReactionsList(
                options=options,
                channel=channel,
                role=role,
                name=name,
                guild=guild,
                message=message
            )
        )


def setup(bot):
    bot.add_cog(Roles(bot))
