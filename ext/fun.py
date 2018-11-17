import discord
from discord.ext import commands

import sql
import random
from imgurpython import ImgurClient
from PIL import Image
import PIL.ImageOps
import requests
import io

class Fun:
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.db = sql.MySQL()

        try:
            self.imgur = ImgurClient('a7a517a27f5cb30', '8587bb31ad9b16494ac4f1b5318bf224f65fd043')
        except:
            print("Imgur Error!")
            self.bot.remove_command("hug")

    @commands.group(name="tag")
    async def tag(self, ctx, *, tag):
        if tag == "create":
            await ctx.invoke(self._tag_create)
            return

        tagRow = self.db.execute(f"SELECT * FROM Tags WHERE Name='{tag}'", 1)
        if tagRow is None:
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description=f"The tag '{tag}' does not exist. You can create it using `!tag create`",
                                               color=0xff0000))
        else:
            await ctx.send(tagRow['Text'])


    @tag.command(name="create")
    async def _tag_create(self, ctx):
        await ctx.send(embed=discord.Embed(title="Tag Creation - Name",
                                           description="Please type the name you wish to use for your tag",
                                           color=0xffff00))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        n = await self.bot.wait_for('message', check=check)
        n = n.content

        ncheck = self.db.execute(f"SELECT * FROM Tags WHERE Name='{n}'", 1)
        if ncheck is not None:
            await ctx.send(embed=discord.Embed(title="ERROR",
                                               description=f"The tag '{n}' already exists!",
                                               color=0xff0000))
            return

        await ctx.send(embed=discord.Embed(title="Tag Creation - Text",
                                           description="Next please type the text you wish for your tag to display",
                                           color=0xffff00))
        t = await self.bot.wait_for('message', check=check)
        t = t.content

        self.db.execute(f"INSERT INTO Tags (Name, OwnerID, Text) VALUES ('{n}', {ctx.author.id}, '{t}')")
        await ctx.send(embed=discord.Embed(title="SUCCESS",
                                           description=f"Your tag has been created, try it by using `!tag {n}`",
                                           color=0x00ff00))

    @commands.command(name="hug", aliases=['cuddle'])
    async def hug(self, ctx, member: discord.Member):
        gifs = self.imgur.get_album_images('Qduvdi6')
        id = random.randint(0, len(gifs) - 1)

        await member.send(embed=discord.Embed(
            description=f"You were hugged by {ctx.author.display_name}",
            color=0xff69b4
        ).set_image(
            url=gifs[id].link
        ))
        await ctx.send("❤")

    @commands.command(name="spookify")
    async def spookify(self, ctx):
        await ctx.author.edit(nick=f"🎃{ctx.author.display_name}👻")
        await ctx.send("👍")

    @commands.command(name="spookifyim")
    async def spookifyim(self, ctx):
        await ctx.trigger_typing()
        im = Image.open(requests.get(ctx.author.avatar_url, stream=True).raw)
        im = im.convert("RGB")
        im = PIL.ImageOps.invert(im)
        b = io.BytesIO()
        im.save(b, "PNG")
        b.seek(0)
        await ctx.send(file=discord.File(b, filename="spooky.png"))



def setup(bot):
    bot.add_cog(Fun(bot))
