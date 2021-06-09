import discord
import random
from discord.ext import commands


class Love(commands.Cog):

    @commands.command()
    async def love(self, ctx, user: commands.Greedy[discord.User]):
        author = ctx.author
        user = user[0]
        love = random.randint(0, 100)
        special = ''
        msg = f"% of love between <@{author.id}> and <@{user.id}>"
        while True:
            if author.id == user.id:
                msg = ' ,Don\'t worry, i bet your mom still loves you'
                love = 'Suck a Fuck'
                break
            else:
                if author.id == 782702698171727902 or user.id == 782702698171727902:  # Amy
                    if author.id == 815045139042402344 or user.id == 815045139042402344:  # Molly
                        love = 200
                        special = 'They do be lovin eachother alot :heart: '
                        break

                if author.id == 129840730565902337 or user.id == 129840730565902337:  # Alice
                    if author.id == 228322335504072705 or user.id == 228322335504072705:  # Jonas
                        love = '[cannot calculate with such high numbers]'
                        special = "It is, as if they are meant for eachother :heart:"
                        break

                    if (author.id == 815045139042402344 or user.id == 815045139042402344    # Molly
                            or author.id == 782702698171727902 or user.id == 782702698171727902  # Amy
                            or author.id == 814693967316254761 or user.id == 814693967316254761  # Peanut
                            or author.id == 762159702275522581 or user.id == 762159702275522581  # TrebleKait
                            or author.id == 756575879362117752 or user.id == 756575879362117752):  # Sheppard

                        love = 100
                        msg = f" of love between <@{author.id}> and <@{user.id}>"
                        special = "this was 100% a correct calculation, and i was not forced to say that. ᵖˡˢ ˢᵉⁿᵈ ʰᵉˡᵖ"
                        break
                    else:
                        break
                else:
                    break

        embed = discord.Embed(description=f"There is {love}" + msg + "\n"
                                          f"{special}",
                              colour=discord.Colour(0xc603fc))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Love(bot))
