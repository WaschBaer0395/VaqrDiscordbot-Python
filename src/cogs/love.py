import discord
import random
from discord.ext import commands

from ext.config import check_config, save_config


class Love(commands.Cog):

    def __init__(self, _bot):
        """Love command, showing love between author and tagged user"""
        self.bot = _bot
        self.conf, self.settings = check_config('LOVE', {'SpecialRoleID': '855830021247729675'})

        self.love = [
            'https://cdn.discordapp.com/attachments/823041335678206042/855552686484488241/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855552752917413898/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855552843448451083/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855552949950480414/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553003384733736/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553146875936778/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553552259481630/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553792019136563/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553884926902300/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855553972529004554/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554128885710868/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554221956530196/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554513167319050/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554577981243442/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554758080069653/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554837721907229/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855554961143889920/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555065698582528/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555140193746954/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555227188330566/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555280346546227/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555360189054986/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855555678949343242/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855556067836035122/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855556205308411984/image0.gif',
        ]

        self.dissapointed = [
            'https://cdn.discordapp.com/attachments/823041335678206042/855894335224414228/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855893912168955904/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855894114003582996/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855894244858527774/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855894438824247316/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/855894494163763220/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856065475871768607/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856065541685248030/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856065625104056431/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856065737886138368/image0.gif'
        ]

        self.eh = [
            'https://cdn.discordapp.com/attachments/823041335678206042/856066020129112084/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856066083454451732/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856066165938847774/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856066323553452062/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856066391728062474/image0.gif',
            'https://cdn.discordapp.com/attachments/823041335678206042/856066433108279317/image0.gif',
            'https://media1.tenor.com/images/71909d2379b8d7c2e8f2826a0ccffd2f/tenor.gif',
        ]

    @commands.command()
    async def love(self, ctx, user: commands.Greedy[discord.User]):
        author = ctx.author
        user = user[0]
        love = random.randint(0, 100)
        image = None
        special = ''
        msg = f"% of love between <@{author.id}> and <@{user.id}>"
        if author.id == user.id:
            msg = ' ,Don\'t worry, i bet your mom still loves you'
            love = 'Suck a Fuck'
            image = 'https://media1.tenor.com/images/77e92c8b0074c06113d04aed22c389e0/tenor.gif'
        else:
            if author.id == 782702698171727902 or user.id == 782702698171727902:  # Amy
                if author.id == 134753100358483968 or user.id == 134753100358483968:  # WaschBaer
                    love = 199
                    special = 'as if its meant to be :3'
                    image = 'https://media1.tenor.com/images/31362a548dc7574f80d01a42a637bc93/tenor.gif'

            elif author.id == 782702698171727902 or user.id == 782702698171727902:  # Amy
                if author.id == 815045139042402344 or user.id == 815045139042402344:  # Molly
                    love = 200
                    special = 'They do be lovi\'n eachother alot :heart: '
                    image = 'https://media1.tenor.com/images/20afd6fa304cd271ba789c45132f6755/tenor.gif'

            elif author.id == 228322335504072705 or user.id == 228322335504072705:  # Jonas
                if author.id == 283056284402712576 or user.id == 283056284402712576:  # Coco
                    love = 169
                    special = 'I think, we all knew about this 😏'
                    image = 'https://media.tenor.com/images/fed38b3f86751a4d342ce6dcb7893ca1/tenor.gif'

            elif author.id == 266805090474655744 or user.id == 266805090474655744:  # Koi
                if author.id == 134753100358483968 or user.id == 134753100358483968:  # WaschBaer
                    love = 9000
                    special = 'a Koi and a Raccoon, obv best friends duh <3'
                    image = 'https://c.tenor.com/iOHpNtWDPpwAAAAC/best-freaking-friends-forever-best-friends.gif'

            elif author.id == 129840730565902337 or user.id == 129840730565902337:  # Alice
                specialroleid = int(self.conf.get('LOVE', 'SpecialRoleID'))
                rolemembers = self.bot.guilds[0].get_role(specialroleid).members
                if author.id == 228322335504072705 or user.id == 228322335504072705:  # Jonas
                    love = '[cannot calculate with such high numbers]'
                    special = "It is, as if they are meant for eachother :heart:"
                    image = 'https://media1.tenor.com/images/7d72269b489123ab2c063e2797a17022/tenor.gif'

                elif author in rolemembers or user in rolemembers:
                    love = 100
                    msg = f" of love between <@{author.id}> and <@{user.id}>"
                    special = "this was 100% a correct calculation, and i was not forced to say that. ᵖˡˢ ˢᵉⁿᵈ ʰᵉˡᵖ"
                    image = 'https://media1.tenor.com/images/dbc4623f698244ceea09883dbb7afe9a/tenor.gif'

            if special == '':
                if love == 69:
                    special = 'Woah 69 , wink wink'
                    image = 'https://media1.tenor.com/images/d3cb268f65351cdb5dadb9a889746875/tenor.gif'
                elif 0 <= love < 40:
                    image = random.choice(self.dissapointed)
                elif 40 <= love < 60:
                    image = random.choice(self.eh)
                else:
                    image = random.choice(self.love)
        embed = discord.Embed(description=f"There is {love}" + msg + "\n"
                                          f"{special}",
                              colour=discord.Colour(0xc603fc))
        if image is not None:
            embed.set_image(url=image)
        await ctx.send(embed=embed)

    @commands.command()
    async def setup_love(self, ctx, role: commands.Greedy[discord.Role]):
        if role[0].id:
            roleid = role[0].id
            self.conf.set('LOVE', 'SpecialRoleID', str(roleid))
            save_config(self.conf)
            embed = discord.Embed(title="Role", colour=discord.Colour(0x269a78),
                                  description=f"Special Role has been set to {role[0].name}")
        else:
            embed = discord.Embed(title="Role", colour=discord.Colour(0x269a78),
                                  description="Please enter a correct Role for the Specialrole")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Love(bot))
