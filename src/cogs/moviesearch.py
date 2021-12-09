import asyncio
import datetime

import discord
from discord import Colour
from discord.ext import commands
from discord import Embed
from imdb import IMDb

bot = commands.Bot('')


def pop_empty_data(data):
    if data is not None and not str:
        for idx, d in enumerate(data):
            if len(d.data) == 0:
                data.pop(idx)
    return data


class MovieSearch(commands.Cog):

    def __init__(self, _bot):
        self.bot = _bot
        self.ia = IMDb()

    @commands.command(aliases=['msearch', 'show_search', 'movie_search', 'movie'])
    async def imdb(self, ctx, *, args=None):
        search = self.ia.search_movie(args)[0]
        url = self.ia.get_imdbURL(search)
        movie = self.ia.get_movie(search.movieID)

        # Creating a title including year and runtime if possible
        title = movie.get('title')
        year = movie.get('year')
        runtime = int(movie.get('runtimes')[0])
        if year:
            title += ' (' + str(year) + ')'
        if runtime:
            runtime = datetime.timedelta(minutes=runtime)
            minutes = int((int(runtime.seconds) % 3600) / 60)
            hours = int(runtime.seconds) // 3600
            runtime = str(hours) + 'h'
            if minutes != 0:
                runtime += ' ' + str(minutes) + 'm'
            title += ' - ' + runtime

        # Creating the description, cutting it of if > 350 chars
        description = movie.get('plot')[0]
        if description is not None and len(description) > 350:
            description = description[:337]
            description += " ... [view more]({})".format(str(url))
        description = '||' + description + '||'

        art = movie.get('cover url')
        url = 'https://www.imdb.com/title/tt' + str(movie.get('imdbID'))
        kind = movie.get('kind').title()

        embed = Embed(
            title=title,
            url=url,
            colour=Colour(0xE5E242),
            description=description)
        embed.set_thumbnail(url=art)
        embed.set_author(name=kind)


        # Formatting list of Directors for embed
        directors = pop_empty_data(movie.get('directors'))
        if directors is not None:
            buff = ''
            for d in directors:
                if len(d.data) != 0:
                    buff += d.data.get('name') + '\n'
            directors = buff
            embed.add_field(name="Director/s", value=directors, inline=True)
        else:
            seasons = movie.get('seasons')
            if seasons is not None:
                embed.add_field(name='Seasons', value=seasons, inline=True)

        # Formatting list of Genres for embed
        genres = pop_empty_data(movie.get('genres'))
        if genres is not None:
            buff = ''
            for g in genres:
                buff += g + '\n'
            genres = buff
            embed.add_field(name="Genre", value=genres, inline=True)

        # Formatting Score for embed
        score = movie.get('rating')
        if score is not None:
            score = str(score)
            votes = movie.get('votes')
            if votes is not None:
                score += ' (' + str(votes) + ' votes)'
            embed.add_field(name="Score", value=score, inline=True)

        # Formatting list of Writers for embed
        writers = pop_empty_data(movie.get('writers'))
        if writers is not None:
            buff = ''
            for w in writers:
                if len(w.data) != 0:
                    buff += w.data.get('name') + ', '
            writers = buff
            embed.add_field(name="Writers", value=writers, inline=False)

        # Formatting list of Cast for embed
        cast = pop_empty_data(movie.get('cast'))
        if cast is not None:
            buff = ''
            for c in cast[:5]:
                if len(c.data) != 0:
                    buff += c.data.get('name') + ', '
            cast = buff
            embed.add_field(name="Cast", value=cast, inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MovieSearch(bot))
