import discord
import configparser
import asyncio
import youtube_dl
import logging
import math

from discord.ext import commands
from ext.music import Media


async def audio_playing(ctx, respond=True):
    """Checks that audio is currently playing before continuing."""
    client = ctx.guild.voice_client
    if client and client.channel and client.source:
        return True
    else:
        if respond:
            embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="The queue is empty")
            await ctx.send(embed=embed)
        return False


async def in_voice_channel(ctx):
    """Checks that the command sender is in the same voice channel as the bot."""
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                              description="You need to be in the voice channel to do that.")
        await ctx.send(embed=embed)
        return False


async def in_voice(ctx):
    """Checks that the command sender is in the same voice channel as the bot."""
    bot_voice = ctx.guild.voice_client
    if bot_voice is not None and bot_voice.channel is not None:
        return True
    else:
        return False


async def is_audio_requester(ctx):
    """Checks that the command sender is the song requester."""
    music = ctx.bot.get_cog("Music")
    state = music.get_state(ctx.guild)
    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator or state.is_requester(ctx.author):
        return True
    else:
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                              description="You need to be the song requester to do that")
        await ctx.send(embed=embed)
        return False


class Music(commands.Cog):

    """Bot commands to help play music."""

    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.bot.add_listener(self.on_voice_state_update, "on_voice_state_update")

    def get_state(self, guild):
        """Gets the state for `guild`, creating it if it does not exist."""
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]

    @commands.command(aliases=["stop"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx):
        """Leaves the voice channel."""
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)
        if client and client.channel:
            await client.disconnect()
            state.playlist = []
            state.now_playing = None

    @commands.command(aliases=["resume"])
    @commands.guild_only()
    @commands.check(is_audio_requester)
    async def pause(self, ctx):
        """Pauses the current media."""

        voice = await in_voice(ctx)
        if voice is False:
            if ctx.author.voice is not None and ctx.author.voice.channel is not None:
                channel = ctx.author.voice.channel
                await channel.connect()
            else:
                embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                      description="You need to be in the voice channel to do that.")
                await ctx.send(embed=embed)

        in_vc = await in_voice_channel(ctx)
        is_playing = await audio_playing(ctx, respond=False)

        state = self.get_state(ctx.guild)
        if in_vc:
            client = ctx.guild.voice_client
            if is_playing and ctx.author.voice is not None and ctx.author.voice.channel is not None:
                await _pause_audio(ctx, client)
            else:
                self._play_song(client, state, state.now_playing)

    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    async def volume(self, ctx, volume: int):
        """Change the media volume (values 0-250)."""
        state = self.get_state(ctx.guild)

        # make sure volume is nonnegative
        if volume < 0:
            volume = 0

        config = check_config()
        max_vol = int(config.get('MUSIC', 'max_volume'))
        if max_vol > -1:  # check if max volume is set
            # clamp volume to [0, max_vol]
            if volume > max_vol:
                volume = max_vol

        client = ctx.guild.voice_client

        state.volume = float(volume) / 100.0
        client.source.volume = state.volume  # update the AudioSource's volume to match
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                              description=f"Music volume set to {state.volume}%")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    async def skip(self, ctx):
        """Skips the currently playing song, or votes to skip it."""
        config = check_config()
        state = self.get_state(ctx.guild)
        client = ctx.guild.voice_client
        if ctx.channel.permissions_for(
                ctx.author).administrator or state.is_requester(ctx.author):
            # immediately skip if requester or admin
            client.stop()
        elif config.get('MUSIC', 'vote_skip'):
            # vote to skip song
            channel = client.channel
            self._vote_skip(channel, ctx.author)
            # announce vote
            users_in_channel = len([
                member for member in channel.members if not member.bot
            ])  # don't count bots
            required_votes = math.ceil(
                config.get('MUSIC', 'vote_skip_ratio') * users_in_channel)
            await ctx.send(
                f"{ctx.author.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)"
            )
        else:
            embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                  description="Vote to skip is disabled :(")
            await ctx.send(embed=embed)

    def _vote_skip(self, channel, member):
        """Register a vote for `member` to skip the song playing."""
        config = check_config()
        logging.info(f"{member.name} votes to skip")
        state = self.get_state(channel.guild)
        state.skip_votes.add(member)
        users_in_channel = len([
            member for member in channel.members if not member.bot
        ])  # don't count bots
        if (float(len(state.skip_votes)) / users_in_channel) >= config.get('MUSIC', 'vote_skip_ratio'):
            # enough members have voted to skip, so skip the song
            print(f"Enough votes, skipping...")
            channel.guild.voice_client.stop()

    def _play_song(self, client, state, song):
        state.now_playing = song
        state.skip_votes = set()  # clear skip votes
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song.stream_url,
                                   before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
            volume=state.volume)

        def after_playing():
            if len(state.playlist) > 0:
                next_song = state.playlist.pop(0)
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.bot.loop)

        client.play(source, after=after_playing)

    @commands.command(aliases=["np"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        """Displays information about the current song."""
        state = self.get_state(ctx.guild)
        await ctx.send("", embed=state.now_playing.get_embed())

    @commands.command(aliases=["q", "playlist"])
    @commands.guild_only()
    async def queue(self, ctx):
        """Displays the current play queue."""
        state = self.get_state(ctx.guild)
        await ctx.send(embed=_queue_text(state.playlist))

    @commands.command(aliases=["cq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def clearqueue(self, ctx):
        """Clears the play queue."""
        state = self.get_state(ctx.guild)
        state.playlist = []

    @commands.command(aliases=["rem"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *args):
        """Remove a song at an index"""
        state = self.get_state(ctx.guild)

        if len(state.playlist) > 0:
            if len(args) > 0:
                if args[0] == "last":
                    index = len(state.playlist) - 1
                    embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                          description=f"🗑️ Removed **{state.playlist[index].title}** from the queue")
                    await ctx.send(embed=embed)
                    state.playlist.pop()
                if args[0] == "next":
                    embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                          description=f"🗑️ Removed **{state.playlist[0].title}** from the queue")
                    await ctx.send(embed=embed)
                    state.playlist.pop(0)

                if args[0].isnumeric():
                    index = int(args[0]) - 1
                    if 0 <= index <= len(state.playlist):
                        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                              description=f"🗑️ Removed **{state.playlist[index].title}** "
                                                          f"from the queue")
                        await ctx.send(embed=embed)
                        state.playlist.pop(index)
            else:
                embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1),
                                      description="Specify the index for the song to remove "
                                                  "(or use \"next\" and \"last\"")
                await ctx.send(embed=embed)

    @commands.command(aliases=["move"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def jump(self, ctx, song: int, new_index: int):
        """Moves song to an index. (usage: jump <old> <new>)."""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 0 <= song <= len(state.playlist) and 1 <= new_index:
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(new_index - 1, song)  # and insert it.

            await ctx.send(embed=_queue_text(state.playlist))
        else:
            raise commands.CommandError("You must use a valid index.")

    @commands.command(aliases=["priority"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def jumpqueue(self, ctx, song: int):
        """Moves song at an index to next in queue."""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 0 <= song <= len(state.playlist):
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(0, song)  # and insert it.

            await ctx.send(embed=_queue_text(state.playlist))
        else:
            raise commands.CommandError("You must use a valid index.")

    @commands.command(aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx, *, url):
        """Plays media hosted at <url> or conducts a search."""
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)  # get the guild's state

        if client and client.channel:
            try:
                video = Media(url, ctx.author)
            except youtube_dl.DownloadError as e:
                logging.warning(f"Error downloading video: {e}")
                await ctx.send("There was an error downloading your video, sorry.")
                return
            state.playlist.append(video)
            await ctx.send(
                "Added to queue.", embed=video.get_embed())
        else:
            if ctx.author.voice is not None and ctx.author.voice.channel is not None:
                channel = ctx.author.voice.channel
                try:
                    video = Media(url, ctx.author)
                except youtube_dl.DownloadError:
                    await ctx.send("There was an error downloading your video, sorry.")
                    return
                client = await channel.connect()
                self._play_song(client, state, video)
                await ctx.send("", embed=video.get_embed())
                logging.info(f"Now playing '{video.title}'")
            else:
                raise commands.CommandError(
                    "You need to be in a voice channel to do that.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel and member.id == 836383111935426621:
            if not before.channel and after.channel is None:
                state = self.get_state(member.guild)
                if not state:
                    client = member.guild.voice_client
                    if not client:
                        client.pause()


async def _pause_audio(ctx, client):
    if client.is_paused():
        client.resume()
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="▶️ Music resumed")
        await ctx.send(embed=embed)
    else:
        client.pause()
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="⏸️ Music paused")
        await ctx.send(embed=embed)


def _queue_text(queue):
    """Returns a block of text describing a given song queue."""
    embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1))
    if len(queue) > 0:
        embed.description = f"{len(queue)} songs in the queue"
        message = ''

        for index, song in enumerate(queue):
            message += f"  `{index + 1}.` **{song.title}** " \
                       f"(requested by {song.requested_by.mention})\n"  # add individual songs
        embed.add_field(name='Song Queue', value=message)
        return embed
    else:
        embed.description = "The queue is empty"
        return embed


def check_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # checking for existing config
    if config.has_section('MUSIC'):
        config.get('MUSIC', 'max_volume')
        config.get('MUSIC', 'vote_skip'),
        config.get('MUSIC', 'vote_skip_ratio'),
    else:
        # writing default config, incase none has been found
        config['MUSIC'] = \
            {
                'max_volume': '250',
                'vote_skip': 'True',
                'vote_skip_ratio': '0.5',
            }
        try:
            with open('settings.ini', 'w+') as configfile:
                config.write(configfile)
        except Exception as e:
            print('```error writing config: ' + str(e) + ' ```')
    return config


def setup(bot):
    bot.add_cog(Music(bot))


class GuildState:
    """Helper class managing per-guild state."""

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user
