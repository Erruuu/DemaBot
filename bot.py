import discord
from discord.ext import commands
import asyncio
import random
import schedule

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io


import sql

ext = [
    "ext.misc",
    "ext.econ",
    "ext.mod",
    "ext.fun"
]

class printCol:
    BOLD = '\033[1m'
    SUCCESS = '\033[92m'
    END = '\033[0m'

class Taco(commands.Bot):
    def __init__(self):
        self.token = open("token.txt").read()
        super().__init__(command_prefix="!", owner_id=356268554494148608)

        self.db = sql.MySQL()

        self.run()

    async def on_ready(self):
        print("LOADING COMMANDS")
        self.remove_command("help")
        for e in ext:
            self.load_extension(e)
            print(" + " + e)
        print("BOT READY")

        for u in self.get_all_members():
            if len(self.db.execute(f"SELECT * FROM Users WHERE ID={u.id}", 2)) == 0:
                self.db.execute(f"INSERT INTO Users (ID) VALUES ({u.id})")

        schedule.every().day.at("00:00").do(self.update_shop)

    def update_shop(self):
        self.db.execute("UPDATE Roles SET InShop=0 WHERE Category='Songs' AND InShop=1")
        self.db.execute("UPDATE Roles SET InShop=1 WHERE Category='Songs' ORDER BY RAND() LIMIT 5")

    async def status_rotate(self):
        await self.wait_until_ready()

        s = 0
        while not self.is_closed():
            schedule.run_pending()
            statuses = [f'{str(sum(not member.bot for member in self.get_guild(470584033668104212).members))} users',
                         '!help']
            await self.change_presence(activity=discord.Activity(name=statuses[s], type=discord.ActivityType.watching))
            if s == len(statuses)-1:
                s = 0
            else:
                s += 1
            await asyncio.sleep(30)

    async def timed_message(self):
        await self.wait_until_ready()
        waitTime = 60
        messageNum = 15
        messages = ["Have you claimed your dailies today? If not then head over to <#470622085279121429> and use `!daily`",
                    "Want to help the server out? Apply for staff here: <https://goo.gl/forms/ZNcSEt8AuZCpbEBA2>",
                    "Is there something you would like adding to the server? Use `!suggest` in <#470622085279121429>"]

        def check(m):
            return int(m.channel.id) == 470584033668104214
        msg = await self.wait_for('message', check=check)
        while not self.is_closed():
            c = 0
            async for m in self.get_channel(470584033668104214).history(after=msg):
                c += 1
            if c >= messageNum:
                msg = await self.get_channel(470584033668104214).send(embed=discord.Embed(description=messages[random.randint(0,len(messages)-1)],
                                                                                          color=0xffff00))
            await asyncio.sleep(waitTime)

    async def on_message(self, message):
        if message.author.bot:
            return

        if len(self.db.execute(f"SELECT * FROM Users WHERE ID={message.author.id}", 2)) == 0:
            self.db.execute(f"INSERT INTO Users (ID) VALUES ({message.author.id})")

        if random.randint(1,100) == 1:
            amt=random.randint(1,50)
            self.db.addMoney(message.author, amt)
            await message.channel.send(f"**<@{message.author.id}> found £{str(amt)}!**")

        await self.process_commands(message)

    async def on_member_join(self, member):
        main = Image.open("img/welcomeimg.png")
        avatar = Image.open(requests.get(member.avatar_url,stream=True).raw)
        avatar = avatar.resize((160, 160))

        draw = ImageDraw.Draw(main)

        font = ImageFont.truetype("fnt/eurostile-bold.ttf", 50)
        name = member.display_name[:9]
        draw.text((226, 60), f"Welcome, @{name}", (0, 0, 0), font=font)

        mask = Image.new('L', (320, 320), 0)
        drawMask = ImageDraw.Draw(mask)
        drawMask.ellipse((0, 0, 320, 320), fill=255)
        mask = mask.resize((160, 160), Image.ANTIALIAS)
        avatar.putalpha(mask)

        main.paste(avatar, (50, 39), avatar)
        b = io.BytesIO()
        main.save(b, "PNG")
        b.seek(0)
        await self.get_channel(470584033668104214).send(file=discord.File(b, filename="welcome.png"))

    async def on_member_remove(self, member):
        await self.get_channel(470584033668104214).send(embed=discord.Embed(description=f":wave: Goodbye {member.display_name} 3;",
                                                                            color=0xff0000))

    #UTILS
    async def kick(self, user, reason, by="N/A"):
        embed = discord.Embed(title="KICK NOTICE",
                              description="You have been kicked from the Skeleton Clique Discord server. If you feel this is a mistake then contact the member of staff who kicked you.",
                              color=0xff7f00)
        embed.add_field(name="REASON", value=reason)
        embed.add_field(name="KICKED BY", value=by)
        await user.send(embed=embed)
        await user.kick()

    async def ban(self, user, reason, by="N/A"):
        embed = discord.Embed(title="BAN NOTICE",
                              description="You have been banned from the Skeleton Clique Discord server. If you feel this is a mistake then contact the member of staff who banned you.",
                              color=0xff0000)
        embed.add_field(name="REASON", value=reason)
        embed.add_field(name="BANNED BY", value=by)
        await user.send(embed=embed)
        await user.ban()

    async def warn(self, user, reason, by="N/A"):
        embed = discord.Embed(title="WARN NOTICE",
                              description="You have been issued a warning on the Skeleton Clique Discord server. Currently these do not add up, but please take this into account to avoid recieving a kick/ban in the future.",
                              color=0xffe100)
        embed.add_field(name="REASON", value=reason)
        embed.add_field(name="ISSUED BY", value=by)
        await user.send(embed=embed)

    def run(self):
        print(printCol.SUCCESS + "STARTING BOT" + printCol.END)
        self.loop.create_task(self.status_rotate())
        self.loop.create_task(self.timed_message())
        super().run(self.token)

Taco()
