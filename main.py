import discord
from discord.ext.commands import Bot
import json
import queue
from discord import Embed, utils
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.mongodb import MongoDBJobStore

f = open('config.json', 'r')
config = json.load(f)

prefix = '!'
bot = Bot(command_prefix=prefix)
extensions = ['exts.posts']
jobstore = {
    'default': MongoDBJobStore(database='posts', collection='posts')
}
sched = AsyncIOScheduler(
    jobstores=jobstore)
sched.start()
q = queue.Queue()


@bot.event
async def on_ready():
    channel = bot.guilds[0].channels[0]
    await channel.send('Now online!')
    print(' Bot is up!')


for e in extensions:
    bot.load_extension(e)
# bot.loop.create_task(add_to_schedular())
bot.run(config.get("BOT_TOKEN"))
