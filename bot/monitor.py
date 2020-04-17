import logging
import time

from discord.ext import commands, tasks
from modules.tweakers import Tweakers
from settings import settings

logger = logging.getLogger(__name__)


class Monitor(commands.Cog):
    """Monitoring functionality"""

    def __init__(self, bot):
        self.bot = bot
        self.tweakers = Tweakers()

    @commands.Cog.listener()
    async def on_ready(self):
        self.watch_tweakers_listings.start()

    def cog_unload(self):
        self.watch_tweakers_listings.cancel()

    @tasks.loop(minutes=settings.TWEAKERS_MONITOR_INTERVAL_M)
    async def watch_tweakers_listings(self):
        for channel_id, product_url in settings.TWEAKERS_MONITOR_URLS:
            await self.tweakers.post_new_listings(self.bot, channel_id, product_url)
            time.sleep(settings.TWEAKERS_MONITOR_SLEEP_S)
