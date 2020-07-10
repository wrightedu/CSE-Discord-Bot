from datetime import datetime
from os.path import exists
from pathlib import Path
from random import randint

import discord
from bing_image_downloader import downloader
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Check if corgis dir exists
        if not exists('corgis'):
            downloader.download('corgi',
                                limit=100,
                                output_dir='corgis',
                                adult_filter_off=False,
                                force_replace=False)

        # Get images from directory
        self.images = []
        for path in Path('corgis').rglob('*.*'):
            self.images.append(path.name)

    ###### ================================== ######
    ######              Commands              ######
    ###### ================================== ######

    @commands.command()
    async def corgme(self, ctx):
        # Pick a random image
        image = self.images[randint(0, len(images) - 1)]
        imagename = image[image.rfind('/') + 1:]

        # Send image
        with open(image, 'rb') as im:
            file = discord.File(im, filename=imagename)
            await ctx.send(imagename, file=file)


def setup(bot):
    bot.add_cog(Fun(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
