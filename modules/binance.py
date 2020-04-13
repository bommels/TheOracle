import json
import logging
import random

import websockets
from discord import Embed

import settings
from modules import utils

logger = logging.getLogger(__name__)


class Binance:
    STREAMS = [
        '!forceOrder@arr', 'btcusdt@aggTrade', 'ethusdt@aggTrade', 'linkusdt@aggTrade', 'bnbusdt@aggTrade',
        'bchusdt@aggTrade', 'trxusdt@aggTrade', 'ltcusdt@aggTrade', 'eosusdt@aggTrade', 'xrpusdt@aggTrade'
    ]

    @staticmethod
    async def watch_spot_events(bot):
        logger.info('Opening Binance Spots WebSocket')
        async with websockets.connect('wss://stream.binance.com:9443/stream?streams={}'.format('/'.join(Binance.STREAMS[1:]))) as websocket:
            async for message in websocket:
                message = json.loads(message)

                if message['stream'].endswith('@aggTrade'):
                    await Binance.send_trade_notification(bot, message)

    @staticmethod
    async def watch_futures_events(bot):
        logger.info('Opening Binance Futures WebSocket')
        async with websockets.connect('wss://fstream.binance.com/stream?streams={}'.format('/'.join(Binance.STREAMS))) as websocket:
            async for message in websocket:
                message = json.loads(message)

                if message['stream'] == '!forceOrder@arr':
                    await Binance.send_liquidation_notification(bot, message)
                elif message['stream'].endswith('@aggTrade'):
                    await Binance.send_trade_notification(bot, message)

    @staticmethod
    async def send_trade_notification(bot, trade):
        trade = trade['data']
        symbol = trade['s']
        is_sell = trade['m']
        quantity, price = float(trade['q']), float(trade['p'])
        usd_value = quantity * price

        if usd_value < settings.BINANCE_MIN_TRADE_VALUE_USD:
            return

        if usd_value < settings.BINANCE_MIN_LIQ_VALUE_USD_ALTCOIN and 'XBT' not in symbol:
            return

        message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
        message_order_type = 'Sell' if is_sell else 'Buy'
        embed = Embed(color=message_color, description='{} **${}** on **{} @ {}**'.format(message_order_type, utils.cool_number(usd_value), symbol, price))
        embed.set_author(name='Binance', url=settings.BINANCE_REF_URL, icon_url='https://pbs.twimg.com/profile_images/1228505754300076034/jecNdLm2_400x400.jpg')

        logger.info('Broadcasting trade message: {}'.format(trade))
        await bot.get_channel(settings.DISCORD_TRADES_CHANNEL).send(embed=embed)

    @staticmethod
    async def send_liquidation_notification(bot, liquidation):
        order = liquidation['data']['o']
        symbol = order['s']
        quantity, price = float(order['q']), float(order['ap'])
        usd_value = quantity * price
        is_sell = order['S'] == 'SELL'

        if usd_value < settings.BINANCE_MIN_LIQ_VALUE_USD and 'XBT' in symbol:
            return

        if usd_value < settings.BINANCE_MIN_LIQ_VALUE_USD_ALTCOIN and 'XBT' not in symbol:
            return

        message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
        message_order_type = 'long' if is_sell else 'sell'
        embed = Embed(color=message_color, description='Liquidated **${}** {} on **{} @ {}**'.format(utils.cool_number(usd_value), message_order_type, symbol, price))
        embed.set_author(name='Binance', url=settings.BINANCE_REF_URL, icon_url='https://pbs.twimg.com/profile_images/1228505754300076034/jecNdLm2_400x400.jpg')

        if usd_value >= settings.LIQUIDATION_THUMBNAIL_MIN_VALUE_USD:
            embed.set_thumbnail(url=random.choice(settings.LIQUIDATION_THUMBNAILS))

        logger.info('Broadcasting liquidation message: {}'.format(order))
        await bot.get_channel(settings.DISCORD_LIQUIDATIONS_CHANNEL).send(embed=embed)
