# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class CopartscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class CarItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    guarantee = scrapy.Field()
    condition = scrapy.Field()
    address = scrapy.Field()
    phone = scrapy.Field()
    sale_date = scrapy.Field()
    seller_data = scrapy.Field()
    lot_number = scrapy.Field()
    odometer = scrapy.Field()
    transmission = scrapy.Field()
    drive = scrapy.Field()
    fuel = scrapy.Field()
    keys = scrapy.Field()
    price = scrapy.Field()
    autocheck = scrapy.Field()
    vin_text = scrapy.Field()
    