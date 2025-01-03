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
    lot_number = scrapy.Field()
    odometer = scrapy.Field()
    title_code = scrapy.Field()
    drive = scrapy.Field()
    fuel = scrapy.Field()
    keys = scrapy.Field()
    price = scrapy.Field()
    transmission = scrapy.Field()
    VIN = scrapy.Field()
    primary_damage = scrapy.Field()
    secondary_damage = scrapy.Field()
    ERV = scrapy.Field()
    cylinders = scrapy.Field()
    body_style = scrapy.Field()
    color = scrapy.Field()
    engine_type = scrapy.Field()
    vehicle_type = scrapy.Field()
    highlights = scrapy.Field()
    notes = scrapy.Field()
    