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
        CREATE TABLE IF NOT EXISTS first_ex (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            lot_number TEXT,
            odometer TEXT,
            transmission TEXT,
            drive TEXT,
            fuel TEXT,
            keys TEXT,
            price TEXT,
            vin_text TEXT,
            primary_damage TEXT,
            secondary_damage TEXT, 
            ERV TEXT, 
            cylinders TEXT, 
            body_style TEXT, 
            color TEXT, 
            engine_type TEXT, 
            vehicle_type TEXT, 
            highlights TEXT, 
            notes TEXT 
        )
        """)
        self.connection.commit()

    def process_item(self, item, spider):
        # Insert data into PostgreSQL
        try:
            self.cursor.execute("""
            INSERT INTO copartauto (
                url, title, guarantee, condition, address, phone, sale_date, 
                seller_data, lot_number, odometer, transmission, drive, fuel, 
                keys, price, autocheck, vin_text, primary_damage, secondary_damage, ERV, 
                cylinders, body_style, color, engine_type, vehicle_type, highlights, notes 
            ) VALUES (
                %(url)s, %(title)s, %(guarantee)s, %(condition)s, %(address)s, %(phone)s, %(sale_date)s, 
                %(seller_data)s, %(lot_number)s, %(odometer)s, %(transmission)s, %(drive)s, %(fuel)s, 
                %(keys)s, %(price)s, %(autocheck)s, %(VIN)s, %(primary_damage)s, %(secondary_damage)s, %(ERV)s, 
                %(cylinders)s, %(body_style)s, %(color)s, %(engine_type)s, %(vehicle_type)s, %(highlights)s, %(notes)s, 
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
