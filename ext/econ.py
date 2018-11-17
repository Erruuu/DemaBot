import discord
from discord.ext import commands
import time
import random
import math
import asyncio
import re

import sql

class Econ:
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.db = sql.MySQL()

    async def confirmTransaction(self, ctx):
        confCode = random.randint(11111, 99999)
        conf = await ctx.channel.send(embed=discord.Embed(
            title="Confirm Donation",
            description=f"Type confirmation code `{str(confCode)}` to complete the transaction",
            color=0xffff00
        ))

        def check(m):
            return (m.content == str(confCode) and m.author == ctx.author) and m.channel == ctx.channel

        try:
            await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await conf.edit(embed=discord.Embed(
                description="Confirmation not sent, transaction cancelled",
                color=0xff0000
            ))
            return False
        else:
            return True

    @commands.command(name="bal", aliases=["balance", "money"])
    async def bal(self, ctx):
        money = self.db.execute(f"SELECT Money FROM Users WHERE ID={ctx.author.id}", 1)['Money']
        await ctx.send(embed=discord.Embed(title=f"You currently have **£{money}**!"))

    @commands.command(name="top", aliases=["leaderboard"])
    async def top(self, ctx):
        page = 1
        users = self.db.execute("SELECT * FROM Users WHERE Money > 0 ORDER BY Money DESC", 2)
        pages = int(math.ceil(len(users) / 10))
        while True:
            top = []
            for i in range(0+(10*(page-1)), 10+(10*(page-1))):
                if len(users)-1 < i:
                    break
                u = users[i]
                user = ctx.guild.get_member(u['ID'])
                if user is None:
                    user = "Left User"
                else:
                    user = user.display_name
                top.append(f"**{str(i+1)}.** {user} - £ {str(u['Money'])}")
            msg = await ctx.send(embed=discord.Embed(title="Top Members",
                                               description="\n".join(top),
                                               color=0x00ff00))

            if not page == 1:
                await msg.add_reaction("◀")
            if not page == pages:
                await msg.add_reaction("▶")

            def check(r, u):
                return u == ctx.author and str(r.emoji) in ['◀', '▶'] and r.message.id == msg.id

            try:
                response, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            response = str(response.emoji)

            await msg.delete()

            if response == "▶":
                page+=1
            elif response == "◀":
                page-=1

    @commands.command(name="daily")
    async def daily(self, ctx):
        user = self.db.user(ctx.author)
        since = time.time() - user['lastDaily']

        if since>86400:
            self.db.addMoney(ctx.author, 100)
            self.db.execute(f"UPDATE Users SET lastDaily={time.time()} WHERE ID={ctx.author.id}")
            if since<108000:
                self.db.execute(f"UPDATE Users SET Streak={user['Streak']+1} WHERE ID={ctx.author.id}")
            else:
                self.db.execute(f"UPDATE Users SET Streak=0 WHERE ID={ctx.author.id}")
            user = self.db.user(ctx.author)
            embed=discord.Embed(title="You have claimed your daily £100!",
                                description=f"{':white_medium_square:'*user['Streak']}{':black_medium_square:'*(7-user['Streak'])}\n",
                                color=0x00ff00)
            embed.set_footer(text="HINT: Use `t!remindme` to set a reminder for tomorrow!")
            if user['Streak'] == 7:
                bonusMoney = random.randint(400,600)
                embed.add_field(name="Streak Bonus",
                                value=f"You reached your 7 day streak and received a bonus **£{bonusMoney}**")
                self.db.addMoney(ctx.author, bonusMoney)
                self.db.execute(f"UPDATE Users SET Streak=0 WHERE ID={ctx.author.id}")
            await ctx.send(embed=embed)

        else:
            m, s = divmod(int(86400 - since), 60)
            h, m = divmod(m, 60)
            await ctx.send(embed=discord.Embed(title="You cannot claim your dailies yet!",
                                               description=f"Try again in {h}h {m}m {s}s",
                                               color=0xff0000))

    @commands.command(name="donate")
    async def donate(self, ctx, user:discord.Member, amt:int):
        bal=self.db.execute(f"SELECT Money FROM Users WHERE ID={ctx.author.id}", 1)['Money']
        print(bal)
        if amt<1:
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description="Amount must be at least £1",
                                               color=0xff0000))
            return
        if not bal>=amt:
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description="You do not have enough money. Use `!bal` to see how much you have",
                                               color=0xff0000))
            return
        self.db.addMoney(user, amt)
        self.db.addMoney(ctx.author, -amt)
        await ctx.send(embed=discord.Embed(title="SUCCESS",
                                           description=f"£{amt} has been taken from your balance and added to {user.name}'s",
                                           color=0x00ff00))

    async def _shop(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        msg = await ctx.send(embed=discord.Embed(title="SHOP - Main Menu",
                                                 description="**1** - Roles\n"
                                                             "**2** - Badges",
                                                 color=ctx.author.color))
        await msg.add_reaction('1⃣')
        await msg.add_reaction('2⃣')
        def check(r, u):
            return u == ctx.author and str(r.emoji) in ['1⃣','2⃣'] and r.message.id == msg.id
        response,user = await self.bot.wait_for('reaction_add', check=check)

        await msg.delete()
        if str(response.emoji) == '1⃣':
            await self._shop_roles(ctx)
        elif str(response.emoji) == '2⃣':
            await self._shop_badges(ctx)

    @commands.command(name="shop", aliases=['store'])
    async def shop(self, ctx):
        msg = await ctx.send(f"<@{ctx.author.id}>",embed=discord.Embed(title="ROLE SHOP",
                                                 description="**1** - Limited\n"
                                                             "**2** - Albums\n"
                                                             "**3** - Songs",
                                                             #"**4** - Custom",
                                                 color=ctx.author.color))
        await msg.add_reaction('1⃣')
        await msg.add_reaction('2⃣')
        await msg.add_reaction('3⃣')
        #await msg.add_reaction('4⃣')
        def check(r, u):
            return u == ctx.author and str(r.emoji) in ['1⃣','2⃣','3⃣','4⃣'] and r.message.id == msg.id

        try:
            response, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
        except asyncio.TimeoutError:
            await msg.delete()
            return

        await msg.delete()

        if str(response.emoji) == '1⃣':
            cat = "Limited"
        elif str(response.emoji) == '2⃣':
            cat = "Albums"
        elif str(response.emoji) == '3⃣':
            cat = "Songs"
        elif str(response.emoji) == '4⃣':
            cat = "Custom"

        items = self.db.execute(f"SELECT * FROM Roles WHERE InShop=1 AND Category='{cat}'", 2)
        shop = []
        for i in items:
            shop.append(f"**{items.index(i)+1}** - <@&{i['roleID']}> - £{i['Price']}")
        msg = await ctx.send(f"<@{ctx.author.id}>",embed=discord.Embed(title=f"ROLE SHOP - {cat}",
                                           description="\n".join(shop)))
        for i in range(0,len(items)):
            await msg.add_reaction(f'{i+1}⃣')
        def check(r, u):
            return u == ctx.author and str(r.emoji) in ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣'] and r.message.id == msg.id

        try:
            response, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
        except asyncio.TimeoutError:
            await msg.delete()
            return

        item = items[int(str(response.emoji)[0])-1]

        await msg.delete()

        if str(item['ID']) in self.db.user(ctx.author)['Roles'].split(","):
            await ctx.send(f"<@{ctx.author.id}>",embed=discord.Embed(title="ERROR",
                                               description="You already own this role, use `!role` to activate it.",
                                               color=0xff0000))
            return
        if self.db.user(ctx.author)['Money'] < item['Price']:
            await ctx.send(f"<@{ctx.author.id}>",embed=discord.Embed(title="ERROR",
                                               description="You cannot afford this item. Use `!bal` to see how much you have.",
                                               color=0xff0000))
            return

        self.db.addMoney(ctx.author, -item['Price'])
        self.db.execute(f"UPDATE Users SET Roles='{self.db.user(ctx.author)['Roles']}{item['ID']},' WHERE ID={ctx.author.id}")

        if await self.confirmTransaction(ctx):
            await ctx.send(f"<@{ctx.author.id}>",embed=discord.Embed(title="SUCCESS",
                                               description=f"You have bought the role `{item['Name']}`. Activate it with `!role`",
                                               color=0x00ff00))

    @commands.command(name="createrole", enabled=False)
    async def createrole(self, ctx):
        await ctx.send(embed=discord.Embed(title="Role Creation",
                                           description="Welcome to the role creation wizard! Creating a custom role costs £3000.\n\n"
                                                       "Please enter your desired name for the role. If you do not wish to continue this wizard will automatically close in 30 seconds",
                                           color=0xffff00))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        n = await self.bot.wait_for('message', check=check)
        n = n.content

        await ctx.send(embed=discord.Embed(title="Role Creation",
                                           description="Next, please type the hex code for your desired color without `#`\n"
                                                       "You can get this from https://htmlcolorcodes.com/color-picker/",
                                           color=0xffff00))
        c = await self.bot.wait_for('message', check=check)
        c = c.content
        if not re.search(r'^(?:[0-9a-fA-F]{3}){1,2}$', c):
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description="Invalid hex provided. E.G: `fce300`\n"
                                                           "Cancelling creation!"))
            return

        r = await ctx.guild.create_role(name=n, color=discord.Color(int(c, 16)))
        self.db.execute(f"INSERT INTO Roles (Name, roleID, Price, InShop, Category) VALUES ('{n}', {r.id}, 1500, 1, 'Custom')")
        iid = self.db.execute(f"SELECT ID FROM Roles WHERE roleID={r.id}", 1)['ID']
        self.db.execute(f"UPDATE Users SET Roles='{self.db.user(ctx.author)['Roles']}{iid},' WHERE ID={ctx.author.id}")
        await ctx.send(embed=discord.Embed(title="SUCCESS",
                                           description=f"Your custom role has been created! You can activate it with `!role`",
                                           color=0x00ff00))

    @commands.command(name="role", aliases=['roles'])
    async def role(self, ctx):
        roles = self.db.user(ctx.author)['Roles'].split(",")[:-1]
        page = 1
        pages = int(math.ceil(len(roles) / 5))
        while True:
            rlist = []
            for r in roles[(5*page)-5:5*page]:
                r = self.db.execute(f"SELECT * FROM Roles WHERE ID={r}", 1)
                rlist.append(f"**{roles.index(str(r['ID']))+1}** - <@&{r['roleID']}>")
            msg = await ctx.send(embed=discord.Embed(title=f"Roles {page}/{pages}",
                                                     description="\n".join(rlist)))


            for i in range(len(rlist)):
                await msg.add_reaction(f'{i+1}⃣')

            if not page == 1:
                await msg.add_reaction("◀")
            if not page == pages:
                await msg.add_reaction("▶")

            def check(r, u):
                return u == ctx.author and str(r.emoji) in ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '◀', '▶'] and r.message.id == msg.id
            try:
                response, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            except asyncio.TimeoutError:
                await msg.delete()
                return
            response = str(response.emoji)

            await msg.delete()

            if response == "▶":
                page+=1
            elif response == "◀":
                page-=1
            else:
                role = roles[((5*(page-1))+int(response[0]))-1]
                role = self.db.execute(f"SELECT * FROM Roles WHERE ID='{role}'", 1)
                r = discord.utils.get(ctx.guild.roles, id=role['roleID'])
                if r in ctx.author.roles:
                    embed=discord.Embed(title="ERROR",
                                        description="You already have this role active!",
                                        color=0xff0000)
                    await ctx.send(embed=embed)
                    return
                await ctx.author.add_roles(r)

                for check in roles:
                    check = self.db.execute(f"SELECT * FROM Roles WHERE ID={check}", 1)
                    if discord.utils.get(ctx.guild.roles, id=check['roleID'])==r:
                        continue
                    check = discord.utils.get(ctx.guild.roles, id=check['roleID'])
                    if check in ctx.author.roles:
                        await ctx.author.remove_roles(check)
                        break

                embed = discord.Embed(title="SUCCESS",
                                      description=f"You have activated your `{role['Name']}` role!",
                                      color=0x00ff00)
                await ctx.send(embed=embed)
                return

    @commands.command(name="slots")
    async def slots(self, ctx, bet:int):
        ITEMS = ["<:tyler:510759603210944514>", "<:top:510759606931292160>", "<:tape:510759608042651648>", "<:josh:510760172592037915> ", "<:clique:510759595686363146>", "<:beanie:510759978978508801>"]

        if self.db.user(ctx.author)['Money'] < bet:
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description="You do not have enough money! Use `!bal` to see how much you have.",
                                               color=0xff0000))
            return

        def spinWheel():
            randomNumber = random.randint(0, len(ITEMS)-1)
            return ITEMS[randomNumber]

        firstWheel = spinWheel()
        secondWheel = spinWheel()
        thirdWheel = spinWheel()

        if firstWheel == secondWheel:
            if firstWheel == thirdWheel:
                win = 4
            else:
                win = 1
        elif firstWheel == thirdWheel:
            win = 1
        elif secondWheel == thirdWheel:
            win = 1
        else:
            win = -1

        self.db.addMoney(ctx.author, bet*win)
        if (win > 0):
            await ctx.send(embed=discord.Embed(title=f"SLOTS | {ctx.author.display_name}",
                                               description=f"{firstWheel} {secondWheel} {thirdWheel}\n"
                                                           f"You win ${str(bet*(win+1))}",
                                               color=0x00ff00))
        else:
            await ctx.send(embed=discord.Embed(title=f"SLOTS | {ctx.author.display_name}",
                                               description=f"{firstWheel} {secondWheel} {thirdWheel}\n"
                                                           f"You lose",
                                               color=0xff0000))


def setup(bot):
    bot.add_cog(Econ(bot))
