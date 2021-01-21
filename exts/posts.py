from discord.ext.commands import Cog, command
from discord import Embed, utils, File
from asyncio import sleep
import json
from utils.db import DB
import os
import requests
import shutil
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.mongodb import MongoDBJobStore
from datetime import datetime as dt, timedelta


async def send_post(post_id, db, config, bot):
    post = await db.get_post(post_id)
    embed = Embed(title=post['post_title'])
    embed.description = post['post_desc']
    if post['post_image_location'] is not None:
        f = File(post["post_image_location"], filename='image.jpg')
        embed.set_image(url=f'attachment://image.jpg')
    channel = utils.get(
        bot.guilds[0].channels, name=config.get("TARGET_CHANNEL"))
    await channel.send(file=f, embed=embed)
    await db.remove_post(post_id)
    os.remove(post['post_image_location'])
    print('Post sent!')


class CustomEmbed(Cog):
    def __init__(self, bot):
        f = open('config.json', 'r')
        self.config = json.load(f)
        self.bot = bot
        self.db = DB()
        jobstore = {
            'mongo': MongoDBJobStore(database='posts', collection='posts')
        }
        self.sched = AsyncIOScheduler(
            jobstores=jobstore)
        self.sched.start()
        app_location = os.getcwd()
        self.download_location = f'{app_location}/images'
        if not os.path.exists(self.download_location):
            os.makedirs(self.download_location)

    @command(name='create_post', aliases=['cp'])
    async def create_custom_embed(self, ctx):
        authorId = ctx.message.author.id

        def check(authorId):
            def inner(message):
                if message.author.id == self.bot.user.id:
                    return False
                if message.channel != ctx.channel:
                    return False
                if message.author.id != authorId:
                    return False
                return True
            return inner

        await ctx.send('Enter new post title?')
        msg = await self.bot.wait_for('message', check=check(authorId))
        post_title = msg.content
        await ctx.send('Enter post description text?')
        msg = await self.bot.wait_for('message', check=check(authorId))
        post_description = msg.content
        await ctx.send('Enter the post date in [YYYY/MM/DD HH:MM] format?')
        msg = await self.bot.wait_for('message', check=check(authorId))
        date = msg.content.split(' ')[0]
        year = int(date.split('/')[0])
        month = int(date.split('/')[1])
        day = int(date.split('/')[2])
        time = msg.content.split(' ')[1]
        hours = int(time.split(':')[0])
        minutes = int(time.split(':')[1])
        post_date = dt(year, month, day, hours, minutes)

        await ctx.send('Upload an image for the post? Enter "done" to finalize the post without an image!')

        def checkForFile(authorId):
            def inner(message):
                if message.author.id == self.bot.user.id:
                    return False
                if message.channel != ctx.channel:
                    return False
                if message.content.lower() == 'done':
                    return True
                if len(message.attachments) == 0:
                    return False
                return True
            return inner

        msg = await self.bot.wait_for('message', check=checkForFile(authorId))
        image_location = None
        if msg.content != 'done':
            # Save the post
            image_url = msg.attachments[0].url
            image_location = f'{self.download_location}/{random.randrange(10000000000)}.jpg'
            await self.download_image(image_url, image_location)
        created_post_id = await self.db.create_post(post_title, post_description, post_image_location=image_location)
        trigger = DateTrigger(run_date=post_date)
        self.sched.add_job(send_post, trigger=trigger,
                           args=[created_post_id, self.db, self.config, self.bot], replace_existing=True)
        await ctx.send(f'Post has been scheduled!')

    async def download_image(self, image_url, path):
        response = requests.get(image_url, stream=True)
        with open(path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)


def setup(bot):
    bot.add_cog(CustomEmbed(bot))
    print(' Posts extesnsion has been loaded!')
