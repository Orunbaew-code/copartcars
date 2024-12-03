# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from datetime import datetime
import pytz
import psycopg2
import time

class CopartscraperPipeline:
    def __init__(self):
        # Connect to PostgreSQL
        self.connection = psycopg2.connect(
            host='localhost',  # Change to your PostgreSQL host
            database='cars',
            user='postgres',
            password='1505'
        )
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        # Create the table if it doesn't exist
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS copartauto (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            guarantee TEXT,
            condition TEXT,
            address TEXT,
            phone TEXT,
            sale_date TIMESTAMP,
            seller_data TEXT,
            lot_number TEXT,
            odometer TEXT,
            transmission TEXT,
            drive TEXT,
            fuel TEXT,
            keys TEXT,
            price TEXT,
            autocheck INT,
            vin_text TEXT
        )
        """)
        self.connection.commit()

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
        
        # Insert data into PostgreSQL
        try:
            self.cursor.execute("""
            INSERT INTO copartauto (
                url, title, guarantee, condition, address, phone, sale_date, 
                seller_data, lot_number, odometer, transmission, drive, fuel, 
                keys, price, autocheck, vin_text
            ) VALUES (
                %(url)s, %(title)s, %(guarantee)s, %(condition)s, %(address)s, %(phone)s, %(sale_date)s, 
                %(seller_data)s, %(lot_number)s, %(odometer)s, %(transmission)s, %(drive)s, %(fuel)s, 
                %(keys)s, %(price)s, %(autocheck)s, %(vin_text)s
            )
            """, item)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()  # Roll back the transaction
            spider.logger.error(f"Error saving item: {e}")
        return item

    def close_spider(self, spider):
        # Close the connection when the spider is done
        self.cursor.close()
        self.connection.close()
