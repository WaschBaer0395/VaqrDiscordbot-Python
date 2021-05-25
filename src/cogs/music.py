import concurrent.futures
import re

import requests
import discord
import configparser
import asyncio
import youtube_dl as ytdl
import logging
import math
import validators

from discord.ext import commands
from ext.paginator import PaginatorSession

playing = False


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


async def _pause_audio(ctx, client):
    if client.is_paused():
        client.resume()
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="▶️ Music resumed")
        await ctx.send(embed=embed)
    else:
        client.pause()
        embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="⏸️ Music paused")
        await ctx.send(embed=embed)


class Music(commands.Cog):
    """Bot commands to help play music."""

    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.bot.add_listener(self.on_voice_state_update, "on_voice_state_update")
        self.state = None
        self.is_playing = False
        self.vc_connected = False
        self.r_channel_id = None
        self.current_index = 0
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }

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
        """Leaves the voice channel"""
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
        _is_playing = await audio_playing(ctx, respond=False)

        state = self.get_state(ctx.guild)
        if in_vc:
            client = ctx.guild.voice_client
            if _is_playing and ctx.author.voice is not None and ctx.author.voice.channel is not None:
                await _pause_audio(ctx, client)
            else:
                self._play_song(client, state, state.now_playing)
                await self.send_playing(state.now_playing)

    async def send_playing(self, song):
        channel = self.bot.get_channel(int(self.r_channel_id))
        await channel.send("Now Playing: ", embed=get_embed(song))

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
        if ctx.channel.permissions_for(ctx.author).administrator or state.is_requester(ctx.author):
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
            required_votes = math.ceil(float(config.get('MUSIC', 'vote_skip_ratio')) * users_in_channel)
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
        users_in_channel = len([member for member in channel.members if not member.bot
                                ])  # don't count bots
        if float(len(state.skip_votes) / users_in_channel) >= float(config.get('MUSIC', 'vote_skip_ratio')):
            # enough members have voted to skip, so skip the song
            print(f"Enough votes, skipping...")
            channel.guild.voice_client.stop()

    def _play_song(self, client, state, song):
        state.now_playing = song
        state.skip_votes = set()  # clear skip votes
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song['stream_url'], **self.FFMPEG_OPTIONS),

            volume=state.volume)

        def after_playing(err):
            self.current_index = self.current_index + 1
            if self.current_index <= len(state.playlist):
                next_song = state.playlist[self.current_index]
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.bot.loop)
                self.vc_connected = False
                self.isplaying = False
        try:
            client.play(source, after=after_playing)
            self.current_index = 1
        except discord.errors.ClientException:
            self.is_playing = False
            self.vc_connected = False
            pass

    @commands.command(aliases=["np"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        """Displays information about the current song."""
        state = self.get_state(ctx.guild)
        await ctx.send("", embed=get_embed(state.now_playing))

    @commands.command(aliases=["q", "playlist"])
    @commands.guild_only()
    async def queue(self, ctx):
        """Displays the current play queue."""
        state = self.get_state(ctx.guild)
        await self._queue_text(ctx, state.playlist)

        # if pindex + 1 == self.current_index:
        #     message += f"\t⬐ current track\n" \
        #                f" ```yaml {index + 1}``` . ```http {song['title']}``` " \
        #                f"(requested by {song['requested_by'].mention})\n" \
        #                f"\t⬑ current track\n"  # add individual songs
        # else:

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
                    embed = discord.Embed(title="Music Player",
                                          colour=discord.Colour(0x1),
                                          description=f"🗑️ Removed **{state.playlist[index]['title']}** from the queue")
                    await ctx.send(embed=embed)
                    state.playlist.pop()
                if args[0] == "next":
                    embed = discord.Embed(title="Music Player",
                                          colour=discord.Colour(0x1),
                                          description=f"🗑️ Removed **{state.playlist[0]['title']}** from the queue")
                    await ctx.send(embed=embed)
                    state.playlist.pop(0)

                if args[0].isnumeric():
                    index = int(args[0]) - 1
                    if 0 <= index <= len(state.playlist):
                        embed = discord.Embed(title="Music Player",
                                              colour=discord.Colour(0x1),
                                              description=f"🗑️ Removed **{state.playlist[index]['title']}**"
                                                          f" from the queue")
                        await ctx.send(embed=embed)
                        state.playlist.pop(index)
            else:
                embed = discord.Embed(title="Music Player",
                                      colour=discord.Colour(0x1),
                                      description=f"Specify the index for the song to remove "
                                                  f"(or use \"next\" and \"last\"")
                await ctx.send(embed=embed)

    @commands.command(aliases=["move"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def jump(self, ctx, song: int, new_index: int):
        """Moves song to an index. (usage: jump <old> <new>)"""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 0 <= song <= len(state.playlist) and 1 <= new_index:
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(new_index - 1, song)  # and insert it.

            await self._queue_text(ctx, state.playlist)
        else:
            embed = discord.Embed(title="Music Player",
                                  colour=discord.Colour(0x1),
                                  description=f"You must enter a valid index.")
            await ctx.send(embed=embed)

    @commands.command(aliases=["priority"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def jumpqueue(self, ctx, song: int):
        """Moves song at an index to next in queue."""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 0 <= song - 1 <= len(state.playlist):
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(0, song)  # and insert it.

            await self._queue_text(ctx, state.playlist)
        else:
            embed = discord.Embed(title="Music Player",
                                  colour=discord.Colour(0x1),
                                  description=f"You must enter a valid index.")
            await ctx.send(embed=embed)

    # PLAY # # # # # # # # # # # #
    @commands.command(aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx, *, url):
        """Plays media hosted at <url> or conducts a search."""

        # client = ctx.guild.voice_client
        self.get_state(ctx.guild)  # get the guild's state

        await self._queue_audio(ctx, url, ctx.author)

    async def play_audio(self, video, requested_by, state, client):
        media = get_media(video, requested_by)

        self._play_song(client, state, media)
        await self.send_playing(media)
        return media

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel and member.id == 836383111935426621:
            if before.channel is not None and after.channel is None:
                state = self.get_state(member.guild)
                if state is not None:
                    client = member.guild.voice_client
                    if client is not None:
                        client.pause()

    async def _queue_audio(self, ctx, url_or_search, requested_by):
        """Plays audio from (or searches for) a URL."""
        self.r_channel_id = ctx.channel.id
        try:
            if user_in_channel(ctx):
                if not self.vc_connected:
                    channel = ctx.author.voice.channel
                    client = await channel.connect()
                    self.vc_connected = True
                with ytdl.YoutubeDL(YTDL_OPTS) as ydl:
                    client = ctx.guild.voice_client
                    state = self.get_state(ctx.guild)  # get the guild's state

                    if not validators.url(url_or_search):
                        if 'lyric' not in url_or_search and 'lyrics' not in url_or_search:
                            url_or_search = url_or_search + ' lyrics'

                    request = ydl.extract_info(url_or_search, download=False)
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = []
                        if "_type" in request and request["_type"] == "playlist" and validators.url(url_or_search):
                            for index, song in enumerate(request['entries']):
                                video = ydl.extract_info(song['url'], download=False)
                                if self.is_playing:
                                    futures.append(executor.submit(add_to_playlist,
                                                                   requested_by=requested_by,
                                                                   ydl=ydl,
                                                                   request=song,
                                                                   state=state,
                                                                   index=index))
                                else:
                                    if user_in_channel(ctx):
                                        # play
                                        try:
                                            media = await self.play_audio(video, requested_by, state, client)
                                            futures.append(executor.submit(add_to_playlist,
                                                                           requested_by=requested_by,
                                                                           ydl=ydl,
                                                                           request=song,
                                                                           state=state))
                                            self.is_playing = True
                                        except Exception:
                                            raise

                            if len(request['entries']) > 1:
                                embed = discord.Embed(title="Music Player",
                                                      colour=discord.Colour(0x1),
                                                      description=f"**{len(request['entries'])}** songs added to the queue\n"
                                                                  f"from Playlist **{request['title']}** "
                                                                  f"by **{request['uploader']}** queued!")
                                await ctx.send(embed=embed)
                        else:
                            if 'entries' in request and len(request['entries']) == 1:
                                request = request['entries'][0]
                            if user_in_channel(ctx):
                                video = ydl.extract_info(request['url'], download=False)
                                if self.is_playing:
                                    futures.append(executor.submit(add_to_playlist,
                                                                   ctx=ctx,
                                                                   requested_by=requested_by,
                                                                   ydl=ydl,
                                                                   request=request,
                                                                   state=state))
                                    await ctx.send('Added to Playlist', embed=get_embed(get_media(video, requested_by)))
                                else:
                                    media = await self.play_audio(video, requested_by, state, client)
                                    futures.append(executor.submit(add_to_playlist,
                                                                   ctx=ctx,
                                                                   requested_by=requested_by,
                                                                   ydl=ydl,
                                                                   request=request,
                                                                   state=state))
                                    self.is_playing = True
                            else:
                                raise NotInSameVc
            else:
                raise NotInSameVc
        except NotInSameVc:
            await ctx.send(embed=discord.Embed(
                title="Music Player",
                colour=discord.Colour(0x1),
                description=f"You need to be in the vc with the bot"))

    async def _queue_text(self, ctx, queue):
        """Returns a block of text describing a given song queue."""
        if len(queue) > 0:

            embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="Retrieving  queue...")
            retrieve_msg = await ctx.send(embed=embed)

            queue_2d = list(divide_chunks(queue, 8))

            embed_pages = []
            index = 1
            for pages in queue_2d:
                message = str("```nim\n")
                song_embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1))
                for pindex, song in enumerate(pages):
                    songtitle = song['title']
                    if len(songtitle) > 51:
                        songtitle = (songtitle[:51] + ' ..')
                    if index == self.current_index-1:
                        message += str("\t⬐ current track\n")
                        message += str("{}. {}\n".format(index, songtitle))
                        message += str("\t⬑ current track\n")  # add individual songs
                    else:
                        message += str("{}. {}\n".format(index, songtitle))
                    index = index + 1
                message += str("```")
                song_embed.add_field(name='Song Queue', value=message)
                embed_pages.append(song_embed)
            await retrieve_msg.delete()
            p_session = PaginatorSession(ctx, footer=f"{len(queue)} songs in the queue", pages=embed_pages)
            await p_session.run()
        else:
            embed = discord.Embed(title="Music Player", colour=discord.Colour(0x1), description="The queue is empty")
            await ctx.send(embed=embed)


def add_to_playlist(requested_by, ydl, request, state, index=1):
    print("-> NR {}".format(str(index)))
    video = ydl.extract_info(request['url'], download=False)
    media = get_media(video, requested_by)
    state.playlist.append(media)


def get_media(video, requested_by):
    media = dict(
        stream_url=video["formats"][0]["url"],
        video_url=video["webpage_url"],
        title=video["title"],
        uploader=video["uploader"] if "uploader" in video else "",
        thumbnail=video["thumbnail"] if "thumbnail" in video else None,
        requested_by=requested_by
    )
    return media


def user_in_channel(ctx):
    if ctx.author.voice is not None and ctx.author.voice.channel is not None:
        return True
    else:
        return False


def is_playing(client):
    if client and client.channel:  # bot is not already in the channel playing music
        return True
    else:
        return False


def add_queue(media):
    print('added to queue')


def divide_chunks(_l, n):
    # looping till length l
    for i in range(0, len(_l), n):
        yield _l[i:i + n]


YTDL_OPTS = {
    "default_search": "ytsearch",
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": "in_playlist"
}


def get_embed(video):
    """Makes an embed out of this Video's information."""
    embed = discord.Embed(title=video['title'], description=video['uploader'], url=video['video_url'])
    embed.set_footer(
        text=f"Requested by {video['requested_by'].name}",
        icon_url=video['requested_by'].avatar_url)
    if video['thumbnail']:
        embed.set_thumbnail(url=video['thumbnail'])
    return embed


def check_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # checking for existing config
    if not config.has_section('MUSIC'):
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


class NotInSameVc(Exception):
    pass


class GuildState:
    """Helper class managing per-guild state."""

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing['requested_by'] == user