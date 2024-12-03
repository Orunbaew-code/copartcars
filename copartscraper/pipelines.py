# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from datetime import datetime
import pytz

class CopartscraperPipeline:
    def process_item(self, item, spider):
        # Remove "Icon" from "condition"
        item['condition'] = item['condition'].replace(" Icon", "")
        
        # Replace "\n" with ", " in the address
        item['address'] = item['address'].replace("\n", ", ")
        
        # Parse and convert "sale_date"
        # Remove "UZT" from the string as it causes parsing issues
        sale_date_str = item['sale_date'].replace(" UZT", "")
        
        # Parse the datetime without timezone
        uzbekistan_time = datetime.strptime(sale_date_str, "Mon. %b %d, %Y %I:%M %p")
        
        # Set timezone to Asia/Tashkent
        uz_tz = pytz.timezone('Asia/Tashkent')
        localized_time = uz_tz.localize(uzbekistan_time)
        
        # Convert to UTC
        utc_time = localized_time.astimezone(pytz.utc)
        item['sale_date'] = utc_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return item
