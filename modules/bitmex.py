import json
import logging
import random
import settings

import websockets
from modules import utils
from discord import Embed

logger = logging.getLogger(__name__)


class Bitmex:
    @staticmethod
    async def watch_events(bot):
        while True:
            try:
                logger.info('Opening BitMEX WebSocket')
                async with websockets.connect('wss://www.bitmex.com/realtime?subscribe=liquidation,trade') as websocket:
                    async for message in websocket:
                        message = json.loads(message)

                        is_liquidation = 'table' in message and message['table'] == 'liquidation'
                        if is_liquidation and message['action'] == 'insert':
                            logger.debug('Received liquidation: {}'.format(message))
                            await Bitmex.send_liquidation_notification(bot, message)

                        is_trade = 'table' in message and message['table'] == 'trade'
                        if is_trade and message['action'] == 'insert':
                            logger.debug('Received trade: {}'.format(message))
                            await Bitmex.send_trade_notification(bot, message)
            except websockets.exceptions.ConnectionClosedError:
                logger.info('Lost connection to BitMEX WebSocket')

    @staticmethod
    async def send_liquidation_notification(bot, liquidation):
        for order in liquidation['data']:
            is_sell = order['side'] == 'Sell'
            quantity, price = float(order['leavesQty']), float(order['price'])
            usd_value = quantity

            if usd_value < settings.BITMEX_MIN_LIQ_VALUE_USD and 'XBT' in order['symbol']:
                continue

            if usd_value < settings.BITMEX_MIN_LIQ_VALUE_USD_ALTCOIN and 'XBT' not in order['symbol']:
                return

            message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
            message_order_type = 'short' if not is_sell else 'long'
            embed = Embed(color=message_color, description='Liquidated **${}** {} on **{} @ {}**'.format(utils.cool_number(usd_value), message_order_type, order['symbol'], price))
            embed.set_author(name='BitMEX', url=settings.BITMEX_REF_URL, icon_url='https://u.terry.sh/tpj.png')

            if usd_value >= settings.LIQUIDATION_THUMBNAIL_MIN_VALUE_USD:
                embed.set_thumbnail(url=random.choice(settings.LIQUIDATION_THUMBNAILS))

            logger.info('Broadcasting liquidation message: {}'.format(order))
            await bot.get_channel(settings.DISCORD_LIQUIDATIONS_CHANNEL).send(embed=embed)

    @staticmethod
    async def send_trade_notification(bot, trade):
        for order in trade['data']:
            is_sell = order['side'] == 'Sell'
            usd_value = order['foreignNotional']

            if not usd_value or usd_value < settings.BITMEX_MIN_TRADE_VALUE_USD:
                continue

            if usd_value < settings.BITMEX_MIN_TRADE_VALUE_USD_ALTCOIN and 'XBT' not in order['symbol']:
                return

            message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
            embed = Embed(color=message_color, description='{} **${}** on **{} @ {}**'.format(order['side'], utils.cool_number(usd_value), order['symbol'], order['price']))
            embed.set_author(name='BitMEX', url=settings.BITMEX_REF_URL, icon_url='https://u.terry.sh/tpj.png')

            logger.info('Broadcasting trade message: {}'.format(order))
            await bot.get_channel(settings.DISCORD_TRADES_CHANNEL).send(embed=embed)
