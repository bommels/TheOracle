import json
import logging
import random
import settings

import websockets
from modules import utils
from discord import Embed

logger = logging.getLogger(__name__)


class FTX:
    @staticmethod
    async def watch_events(bot):
        while True:
            try:
                logger.info('Opening FTX WebSocket')
                async with websockets.connect('wss://ftx.com/ws/') as websocket:
                    # Subscribe to market trades
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'BTC-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'ETH-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'LINK-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'XTZ-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'BNB-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'DOGE-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'BSV-PERP'}))
                    await websocket.send(json.dumps({'op': 'subscribe', 'channel': 'trades', 'market': 'SXP-PERP'}))

                    async for message in websocket:
                        message = json.loads(message)

                        if message['channel'] == 'trades' and message['type'] == 'update':
                            for trade in message['data']:
                                value = trade['price'] * trade['size']
                                is_liquidation = trade['liquidation']

                                if is_liquidation:
                                    logger.debug('Received liquidation: {}'.format(trade))
                                    await FTX.send_liquidation_notification(bot, message['market'], trade)
                                else:
                                    logger.debug('Received trade: {}'.format(trade))
                                    await FTX.send_trade_notification(bot, message['market'], trade)
            except websockets.exceptions.ConnectionClosedError:
                logger.info('Lost connection to FTX WebSocket')

    @staticmethod
    async def send_liquidation_notification(bot, market, trade):
        is_sell = trade['side'] == 'sell'
        quantity, price = float(trade['size']), float(trade['price'])
        usd_value = quantity

        if usd_value < settings.FTX_MIN_LIQ_VALUE_USD and 'BTC' in market:
            return

        if usd_value < settings.FTX_MIN_LIQ_VALUE_USD_ALTCOIN and 'BTC' not in market:
            return

        message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
        message_order_type = 'short' if not is_sell else 'long'
        embed = Embed(color=message_color, description='Liquidated **${}** {} on **{} @ {}**'.format(utils.cool_number(usd_value), message_order_type, market, price))
        embed.set_author(name='FTX', url=settings.FTX_REF_URL, icon_url='https://u.terry.sh/is6.jpg')

        if usd_value >= settings.LIQUIDATION_THUMBNAIL_MIN_VALUE_USD:
            embed.set_thumbnail(url=random.choice(settings.LIQUIDATION_THUMBNAILS))

        logger.info('Broadcasting liquidation message: {}'.format(trade))
        await bot.get_channel(settings.DISCORD_LIQUIDATIONS_CHANNEL).send(embed=embed)

    @staticmethod
    async def send_trade_notification(bot, market, trade):
        is_sell = trade['side'] == 'sell'
        quantity, price = float(trade['size']), float(trade['price'])
        usd_value = quantity * price

        if not usd_value or usd_value < settings.FTX_MIN_TRADE_VALUE_USD:
            return

        if usd_value < settings.FTX_MIN_TRADE_VALUE_USD_ALTCOIN and 'BTC' not in market:
            return

        message_color = int('3CBA54', 16) if not is_sell else int('DB3236', 16)
        embed = Embed(color=message_color, description='{} **${}** on **{} @ {}**'.format(trade['side'].upper(), utils.cool_number(usd_value), market, trade['price']))
        embed.set_author(name='FTX', url=settings.FTX_REF_URL, icon_url='https://u.terry.sh/is6.jpg')

        logger.info('Broadcasting trade message: {}'.format(trade))
        await bot.get_channel(settings.DISCORD_TRADES_CHANNEL).send(embed=embed)
