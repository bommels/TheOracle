from discord.ext import commands, tasks
from modules.bitmex import Bitmex
from modules.binance import Binance


class Crypto(commands.Cog):
    """Cryptocurrency functionality"""

    def __init__(self, bot):
        self.bot = bot
        self.watch_bitmex.start()
        self.watch_binance_futures.start()
        self.watch_binance_spot.start()

    def cog_unload(self):
        self.watch_bitmex.cancel()
        self.watch_binance_futures.cancel()
        self.watch_binance_spot.cancel()

    @tasks.loop(hours=1)
    async def watch_bitmex(self):
        await Bitmex.watch_events(self.bot)

    @tasks.loop(hours=1)
    async def watch_binance_futures(self):
        await Binance.watch_futures_events(self.bot)

    @tasks.loop(hours=1)
    async def watch_binance_spot(self):
        await Binance.watch_spot_events(self.bot)
