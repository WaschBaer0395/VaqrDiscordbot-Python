import datetime

import discord
from discord import Colour
from discord.ext import commands
from discord import Embed
from imdb import IMDb

bot = commands.Bot('')
debug = True


def printd(item):
    if debug:
        print(item)


def pop_empty_data(data):
    if data is not None and not str:
        for idx, d in enumerate(data):
            if len(d.data) == 0:
                data.pop(idx)
    return data


class Movie:
    def __init__(self, movie):
        printd('-> getting kind')
        self.kind = movie.get('kind').title()
        printd('-> getting cover')
        self.art = movie.get('cover url')
        printd('-> getting url')
        self.url = 'https://www.imdb.com/title/tt' + str(movie.get('imdbID'))
        printd('-> getting year')
        self.year = movie.get('year')
        printd('-> getting runtime')
        self.runtime = int(movie.get('runtimes')[0])
        printd('-> getting title')
        self.title = movie.get('title')
        printd('-> formatting title')
        self.format_title(year=self.year, runtime=self.runtime)
        printd('-> formatting plot')
        self.description = self.format_description(movie.get('plot'))
        printd('-> getting seasons')
        self.seasons = movie.get('seasons')
        printd('-> getting directors')
        self.directors = movie.get('directors')
        printd('-> getting rating')
        self.score = movie.get('rating')
        printd('-> getting votes')
        self.votes = movie.get('votes')
        printd('-> getting cast')
        self.cast = movie.get('cast')
        printd('-> getting writers')
        self.writers = movie.get('weiters')
        printd('-> getting genres')
        self.genres = movie.get('genres')
        printd('-> done getting information')

    def get_embed(self):
        printd('=> creating embed')
        embed = Embed(title=self.title, url=self.url, colour=Colour(0xE5E242), description=self.description)
        printd('=> setting thumbnail')
        embed.set_thumbnail(url=self.art)
        printd('=> setting title')
        embed.set_author(name=self.kind)

        printd('=> adding directors')
        embed = self.format_directors(embed=embed)
        printd('=> adding genres')
        embed = self.format_genres(embed=embed)
        printd('=> adding score/votes')
        embed = self.format_score(embed=embed)
        printd('=> adding writers')
        embed = self.format_writers(embed=embed)
        printd('=> adding cast')
        embed = self.format_cast(embed=embed)
        printd('=> done creating embed')
        return embed

    def get_kind(self):
        return self.kind

    def format_title(self, year, runtime):
        if year:
            self.title += ' (' + str(year) + ')'
        if runtime:
            runtime = datetime.timedelta(minutes=runtime)
            minutes = int((int(runtime.seconds) % 3600) / 60)
            hours = int(runtime.seconds) // 3600
            runtime = str(hours) + 'h'
            if minutes != 0:
                runtime += ' ' + str(minutes) + 'm'
            self.title += ' - ' + runtime

    def format_description(self, plot):
        description = ''
        if plot is not None:
            for line in plot:
                description += line + ' '
            if len(description) > 350:
                description = description[:337]
                description += " ... [view more]({})".format(str(self.url))
            return '||' + description + '||'
        else:
            return 'No plot available on IMDb'

    def format_directors(self, embed: discord.Embed):
        if self.directors is not None:
            buff = ''
            for d in self.directors:
                if len(d.data) != 0:
                    buff += d.data.get('name') + '\n'
            self.directors = buff
            embed.add_field(name="Director/s", value=self.directors, inline=True)
        else:
            if self.seasons is not None:
                embed.add_field(name='Seasons', value=self.seasons, inline=True)
        return embed

    def format_genres(self, embed: discord.Embed):
        if self.genres is not None:
            buff = ''
            for g in self.genres:
                buff += g + '\n'
            self.genres = buff
            embed.add_field(name="Genre", value=self.genres, inline=True)
        return embed

    def format_score(self, embed: discord.Embed):
        if self.score is not None:
            score = str(self.score)
            if self.votes is not None:
                score += ' (' + str(self.votes) + ' votes)'
            embed.add_field(name="Score", value=self.score, inline=True)
        return embed

    def format_writers(self, embed: discord.Embed):
        if self.writers is not None:
            buff = ''
            for w in self.writers:
                if len(w.data) != 0:
                    buff += w.data.get('name') + ', '
            self.writers = buff
            embed.add_field(name="Writers", value=self.writers, inline=False)
        return embed

    def format_cast(self, embed: discord.Embed):
        if self.cast is not None:
            buff = ''
            for c in self.cast[:5]:
                if len(c.data) != 0:
                    buff += c.data.get('name') + ', '
            self.cast = buff
            embed.add_field(name="Cast", value=self.cast, inline=False)
        return embed


class MovieSearch(commands.Cog):

    def __init__(self, _bot):
        """Movie command to show imdb embed for a movie, or show."""
        self.bot = _bot
        self.ia = IMDb()
        self.message = None
        self.search = None

    @commands.command(aliases=['msearch', 'show_search', 'movie_search', 'movie'])
    async def imdb(self, ctx, *, args=None):
        embed = Embed(colour=Colour(0xE5E242))
        embed.set_author(name='Loading Database...')
        embed.set_image(url='https://i.pinimg.com/originals/97/e9/42/97e942ce7fc4e9d4ea6d844a382f251f.gif')
        self.message = await ctx.send(embed=embed)

        movie = Movie(self.ia.get_movie(self.ia.search_movie(args)[0].movieID))
        embed = movie.get_embed()
        if len(embed.Empty) == 0:
            embed = Embed(colour=Colour(0xE5E242),
                          description='No Movie or Show found\n'
                                      'Please make sure the name is spelled correct\n'
                                      'or add the year to the title')
            await self.message.edit(content=None, embed=embed)
        elif movie.get_kind() == 'Tv Series':
            print('Embed for TV Series')
            #view = MovieView(movie.get('seasons'))
            await self.message.edit(content=None, embed=embed)
        elif movie.get_kind() == 'Movie':
            print('Embed for Movie')
            await self.message.edit(content=None, embed=embed)


class Dropdown(discord.ui.Select):
    def __init__(self, seasons):
        # Set the options that will be presented inside the dropdown
        options = []
        self.restseasons = 0
        self.seasons = seasons
        if self.seasons > 24:
            self.restseasons = self.seasons-23
            self.seasons = 23
        for idx in range(0, self.seasons+1, 1):
            if self.restseasons != 0 and idx == 23:
                options.append(discord.SelectOption(label='More ...'))
            elif idx != 0:
                options.append(discord.SelectOption(label='Season ' + str(idx)))
            else:
                options.append(discord.SelectOption(label='To Summary'))

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Choose a Season", min_values=1, max_values=1, options=options,)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        if self.values[0] == 'More ...':
            await interaction.response.edit_message(view=MovieView(self.restseasons))
        else:
            await interaction.response.send_message(
                f"Selected Season is: {self.values[0]}"
            )


class MovieView(discord.ui.View):
    def __init__(self, seasons):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(seasons))


def setup(bot):
    bot.add_cog(MovieSearch(bot))
