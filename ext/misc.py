import discord
from discord.ext import commands
import asyncio

import sql

import time

class Misc:
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.db = sql.MySQL()

    @commands.command(name="ping")
    async def ping(self, ctx):
        ptime = time.time()
        tmp = await ctx.channel.send(embed=discord.Embed(
            title="Pong!",
            description="Time taken: --",
            color=0x2ecc71
        ))
        ping = time.time() - ptime
        await tmp.edit(embed=discord.Embed(
            title="Pong!",
            description="Time taken: {0:.01f}ms".format(ping),
            color=0x2ecc71
        ))


    @commands.command(name="help", aliases=['commands'])
    async def help(self, ctx, command=None):
        commands = {
            'UTILITY' : {
                'help' : {
                    'description' : 'Displays commands for DemaBot',
                    'usage' : '!help [command]'
                },
                'ping' : {
                    'description' : 'PONG!',
                    'usage' : '!ping'
                }
            },
            'FUN' : {
                'tag' : {
                    'description' : 'Allows you to create a tag that others can use',
                    'usage' : '!tag` `!tag create'
                },
                'hug' : {
                    'description' : 'Send a cute hug gif to another user',
                    'usage' : '!hug [user]'
                }
            },
            'ECONOMY' : {
                'bal' : {
                    'description' : 'Displays your current balance',
                    'usage' : '!bal'
                },
                'top' : {
                    'description' : 'Lists the richest users in the server',
                    'usage' : '!top'
                },
                'daily' : {
                    'description' : 'Gives you £100 every day plus a bonus reward for a 7 day streak',
                    'usage' : '!daily'
                },
                'donate' : {
                    'description' : 'Donate money to another user',
                    'usage' : '!donate [@user] [amount]'
                },
                'shop' : {
                    'description' : 'Displays the shop and allows you to buy items',
                    'usage' : '!shop'
                },
                'role' : {
                    'description' : 'Allows you to choose from your purchased roles',
                    'usage' : '!role'
                }
            }
        }
        if command is None:
            embed = discord.Embed(title="Help for DemaBot")
            embed.set_footer(text="Use `!help [command]` for more info")
            for name, cat in commands.items():
                coms = []
                for cname, com in cat.items():
                    coms.append(f"**{cname}** - {com['description']}")
                embed.add_field(name=name.upper(), value='\n'.join(coms), inline=False)
            await ctx.send(embed=embed)
        else:
            found = False
            for cat in commands.values():
                for name, com in cat.items():
                    if name == command:
                        embed = discord.Embed(title=f"Help for {name}")
                        embed.add_field(name='Description', value=com['description'], inline=False)
                        embed.add_field(name='Usage', value=f"`{com['usage']}`", inline=False)
                        await ctx.send(embed=embed)
                        found = True
                        return
                if found == True:
                    return
            if found == False:
                embed = discord.Embed(title="ERROR",
                                      description="The command you entered could not be found. Use `!help` to view a list of commands.")
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
