import discord
from discord.ext import commands

import sql

import asyncio


class Mod:
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.db = sql.MySQL()

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user:discord.Member, *, reason="N/A"):
        await self.bot.kick(user, reason, by="<@"+str(ctx.author.id)+">")
        await ctx.send("User has been kicked")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user:discord.Member, *, reason="N/A"):
        await self.bot.ban(user, reason, by="<@"+str(ctx.author.id)+">")
        await ctx.send("User has been banned")

    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, user:discord.Member, *, reason="N/A"):
        await self.bot.warn(user, reason, by="<@"+str(ctx.author.id)+">")
        await ctx.send("User has been warned")

    @commands.command(name="say")
    @commands.is_owner()
    async def say(self, ctx, *, msg):
        await ctx.channel.send(msg)
        await ctx.message.delete()

    #OWNER
    @commands.command(name="addmoney", aliases=['givemoney'])
    @commands.is_owner()
    async def addmoney(self, ctx, user:discord.Member, amt:int):
        print("huh")
        self.db.addMoney(user, amt)
        embed=discord.Embed(title=f"Added £{str(amt)} to {user.name}'s balance",
                            color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(name="giverole", aliases=['addrole'])
    @commands.is_owner()
    async def giverole(self, ctx, user:discord.Member, *, item):
        item=item.lower()
        item = self.db.execute(f"SELECT * FROM Roles WHERE Name='{item}'", 1)
        if item is None:
            embed=discord.Embed(title="ERROR",
                                description="The item you entered does not exist. Use `!shop list` to see a list of items.",
                                color=0xff0000)
            await ctx.send(embed=embed)
            return

        inventory = str(self.db.execute(f"SELECT Roles FROM Users WHERE ID={user.id}",1)['Roles'])

        if str(item['ID']) in inventory:
            embed=discord.Embed(title="ERROR",
                                description="User already has role!",
                                color=0xff0000)
            await ctx.send(embed=embed)
            return

        newinv = inventory+f"{item['ID']},"
        self.db.execute(f"UPDATE Users SET Roles='{newinv}' WHERE ID={user.id}")
        embed=discord.Embed(title="SUCCESS",
                            description=f"{user.name} has been given role `{item['Name']}`",
                            color=0x00ff00)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Mod(bot))
