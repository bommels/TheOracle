import logging
import time

from discord import Embed

from settings import settings

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Tweakers:
    saved_listings = {}

    @staticmethod
    def _get_headers():
        return {
            'Cookie': '__Secure-TnetID={}'.format(settings.TWEAKERS_SESSION_TOKEN)
        }

    @staticmethod
    def _get_html(url):
        try:
            logger.info('[GET] {}'.format(url))
            r = requests.get(url, headers=Tweakers._get_headers(), timeout=10)
            if r.status_code == 200:
                return r.text
            else:
                logger.error('Received status_code {} on {}'.format(r.status_code, r.url))
        except requests.Timeout:
            logger.info('Received time-out on {}'.format(url))
        except Exception as e:
            logger.error(e)

        return None

    @staticmethod
    def get_pricewatch_item_listings(url):
        found_listings = []
        response = Tweakers._get_html(url)
        if response:
            source = BeautifulSoup(response, 'html.parser')
            listings = source.find('table', {'class': 'shop-listing'})
            if listings:
                listings = listings.find_all('tr')
                for listing in listings:
                    shop = listing.find('td', {'class': 'shop-name'})
                    if shop:
                        shop = shop.find('p').find('a')
                        shop_name, product_url = shop.text.replace('\n', ''), shop['href']
                        product_price = listing.find('td', {'class': 'shop-price'}).find('p').text.replace('\n', '')[1:]

                        logger.info('Found {} listing for {}'.format(shop_name, product_price))
                        found_listings.append({'shop_name': shop_name, 'product_url': product_url, 'product_price': product_price})

        return found_listings

    def check_for_new_listings(self, url):
        new_listings = []
        listings = self.get_pricewatch_item_listings(url)

        # First run, save all current listings
        if url not in self.saved_listings:
            self.saved_listings[url] = listings

        for listing in listings:
            if listing not in self.saved_listings[url]:  # If new listing
                new_listings.append(listing)

        self.saved_listings[url] = listings
        return new_listings

    async def post_new_listings(self, bot, channel_id, url):
        new_listings = self.check_for_new_listings(url)
        for new_listing in new_listings:
            embed = Embed(color=int('DB3236', 16), description='Found new listing for <{}>.'.format(url))
            embed.set_author(name='Tweakers', icon_url='https://ic.tweakimg.net/ext/i/2000677500.jpeg', url=url)
            embed.add_field(name='Shop', value='[{}]({})'.format(new_listing['shop_name'], new_listing['product_url']), inline=True)
            embed.add_field(name='Price', value=new_listing['product_price'], inline=True)
            await bot.get_channel(channel_id).send(embed=embed)
