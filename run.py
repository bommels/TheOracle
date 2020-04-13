import logging
import settings
from discord.ext import commands
from bot.general import General
from bot.crypto import Crypto

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', level=logging.INFO)

if __name__ == '__main__':
    bot = commands.Bot(command_prefix=settings.DISCORD_COMMAND_PREFIX)

    # Add Cogs here
    bot.add_cog(General(bot))
    bot.add_cog(Crypto(bot))

    # Start bot
    bot.run(settings.DISCORD_BOT_TOKEN)
