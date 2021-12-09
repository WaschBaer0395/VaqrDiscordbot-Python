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


def format_description(description, url):
    if description is not None and len(description) > 350:
        description = description[:337]
        description += " ... [view more]({})".format(str(url))
    description = '||' + description + '||'
    return description


def format_genres(genres, embed: discord.Embed):
    if genres is not None:
        buff = ''
        for g in genres:
            buff += g + '\n'
        genres = buff
        embed.add_field(name="Genre", value=genres, inline=True)
    return embed, genres


def format_directors(directors, embed: discord.Embed, movie):
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
    return embed, directors


def format_score(score, embed: discord.Embed, movie):
    if score is not None:
        score = str(score)
        votes = movie.get('votes')
        if votes is not None:
            score += ' (' + str(votes) + ' votes)'
        embed.add_field(name="Score", value=score, inline=True)
    return embed, score


def format_writers(writers, embed: discord.Embed):
    if writers is not None:
        buff = ''
        for w in writers:
            if len(w.data) != 0:
                buff += w.data.get('name') + ', '
        writers = buff
        embed.add_field(name="Writers", value=writers, inline=False)
    return embed, writers


def format_cast(cast, embed: discord.Embed):
    if cast is not None:
        buff = ''
        for c in cast[:5]:
            if len(c.data) != 0:
                buff += c.data.get('name') + ', '
        cast = buff
        embed.add_field(name="Cast", value=cast, inline=False)
    return embed, cast


def create_title(year, title, runtime):
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
    return title


class MovieSearch(commands.Cog):

    def __init__(self, _bot):
        """Movie command to show imdb embed for a movie, or show."""
        self.bot = _bot
        self.ia = IMDb()

    @commands.command(aliases=['msearch', 'show_search', 'movie_search', 'movie'])
    async def imdb(self, ctx, *, args=None):
        search = self.ia.search_movie(args)[0]
        url = self.ia.get_imdbURL(search)
        movie = self.ia.get_movie(search.movieID)

        # Creating a title including year and runtime if possible
        title = create_title(year=movie.get('year'), title=movie.get('title'), runtime=int(movie.get('runtimes')[0]))

        # Creating the description, cutting it of if > 350 chars
        description = movie.get('plot')[0]
        description = format_description(description=description, url=url)

        art = movie.get('cover url')
        url = 'https://www.imdb.com/title/tt' + str(movie.get('imdbID'))
        kind = movie.get('kind').title()

        embed = Embed(title=title, url=url, colour=Colour(0xE5E242), description=description)
        embed.set_thumbnail(url=art)
        embed.set_author(name=kind)

        # Formatting list of Directors for embed
        embed, _ = format_directors(directors=pop_empty_data(movie.get('directors')), embed=embed, movie=movie)

        # Formatting list of Genres for embed
        embed, _ = format_genres(genres=pop_empty_data(movie.get('genres')), embed=embed)

        # Formatting Score for embed
        embed, _ = format_score(score=movie.get('rating'), embed=embed, movie=movie)

        # Formatting list of Writers for embed
        embed, _ = format_writers(writers=pop_empty_data(movie.get('writers')), embed=embed)

        # Formatting list of Cast for embed
        embed, _ = format_cast(cast=pop_empty_data(movie.get('cast')), embed=embed)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MovieSearch(bot))
