import scrapy
import json
import time
from ..items import CarItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.selector import Selector

class CopartSpider(scrapy.Spider):
    name = "copartspider"
    start_urls = ["https://www.copart.com/lotSearchResults"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Chrome options for headless mode
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--disable-software-rasterizer")

        service = Service(executable_path="chromedriver.exe")  # Update the path to your ChromeDriver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    car_urls = []
    # Use Selenium to navigate and scrape
    def start_requests(self):
        self.driver.get("https://copart.com/lotSearchResults/")

        # Wait for the table rows to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@id='pr_id_2-table']//tr"))
        )
        
        self.car_urls = []
        # Scrape links from the table
        rows = self.driver.find_elements(By.XPATH, "//table[@id='pr_id_2-table']//tr")
        for row in rows:
            try:
                car_link_element = row.find_element(By.TAG_NAME, "a")
                car_url = car_link_element.get_attribute("href")
                if car_url:
                    self.car_urls.append(car_url)
            except Exception as e:
                self.logger.warning(f"Failed to process row: {e}")
        
        # Now yield requests for each car URL to parse_car_page
        yield SeleniumRequest(url=self.car_urls[0], callback=self.parse_car_page)

    def parse_car_page(self, response):                 
        cars_count = 0
        while cars_count<len(self.car_urls):
            
            car_url = self.car_urls[cars_count]
            self.driver.get(car_url)
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h1.p-m-0"))
            )
            
            title = response.css("h1.p-m-0::text").get()
            guarantee = response.css("span.p-border-bottom-dark-gray-3.p-ml-2::text").get()
            condition = response.css("img.lotIcon.lotIcon-CERT-D::attr(alt)").get()
            address = response.css("div:contains('ADDRESS') + div span::text").getall()
            phone = response.css("div:contains('PHONE') + div::text").get()
            sale_date = response.css("span.text-blue font_family_lato_bold p-border-bottom-light-blue p-cursor-pointer p-text-nowrap::text").get()
            seller_data = response.css("span.p-ml-2 ng-star-inserted::text").get()

            #______________________Lot datas______________________ 
            lot_details = {}
            lot_info_sections = response.xpath("//div[@class='lot-details-info']")

            for section in lot_info_sections:
                # Extract label (field name) and value
                label = section.xpath(".//label[contains(@class, 'lot-details-label')]/text()").get()
                value = section.xpath(".//span[contains(@class, 'lot-details-value')]//text()").getall()
                value = " ".join(value).strip()  # Combine and clean value texts

                if label and value:
                    lot_details[label.strip().rstrip(":")] = value
            #______________________Lot datas______________________ 

            price = response.css("h1.p-mt-0 amount bidding-heading p-d-inline-block p-position-relative separate-currency-symbol ng-star-inserted::text").get()
            autocheck = response.css("strong.ldt5-blue-text ng-star-inserted::text").get()

            self.logger.info(f"Scraped Title: {title}")

            # Check if lot_details contains the keys before accessing them to avoid KeyErrors
            lot_number = lot_details.get("Lot Number")
            odometer = lot_details.get("Odometer")
            transmission = lot_details.get("Transmission")
            drive = lot_details.get("Drive")
            fuel = lot_details.get("Fuel")
            keys = lot_details.get("Keys")
            self.logger.info(f"Scraped Title: {title}")

            carItem = CarItem()

            # Assign values to the carItem fields
            carItem["url"] = car_url
            carItem["title"] = title
            carItem["guarantee"] = guarantee
            carItem["condition"] = condition
            carItem["address"] = address
            carItem["phone"] = phone
            carItem["sale_date"] = sale_date
            carItem["seller_data"] = seller_data
            carItem["lot_number"] = lot_number
            carItem["odometer"] = odometer
            carItem["transmission"] = transmission
            carItem["drive"] = drive
            carItem["fuel"] = fuel
            carItem["keys"] = keys
            carItem["autocheck"] = autocheck
            
            with open('car_data.txt', 'a') as file:
                # Convert carItem dictionary to a string (JSON format)
                car_item_str = json.dumps(dict(carItem), ensure_ascii=False, indent=4)
                file.write(car_item_str + '\n')
            
            yield carItem
            cars_count += 1  