import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse
from ..items import CarItem
import time

cars_count = 0

class CopartSpider(scrapy.Spider):
    name = "copartspider"
    allowed_domains = ["copart.com"]

    # Selenium setup
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        
        service = Service(executable_path="chromedriver.exe")  # Update the path to your ChromeDriver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    # Use Selenium to navigate and scrape
    def start_requests(self):
        global cars_count
        self.driver.get("https://copart.com/lotSearchResults/")

        # Wait for table rows to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@id='pr_id_2-table']//tr"))
        )

        # Scrape links from the table
        rows = self.driver.find_elements(By.XPATH, "//table[@id='pr_id_2-table']//tr")
        for row in rows:
            try:
                car_link_element = row.find_element(By.TAG_NAME, "a")
                car_url = car_link_element.get_attribute("href")
                if car_url:
                    # Yield Scrapy request for each car URL
                    yield scrapy.Request(car_url, callback=self.parse_car_page)
            except Exception as e:
                self.logger.warning(f"Failed to process row: {e}")

        # Close the browser after scraping
        self.driver.quit()

    def parse_car_page(self, response):
        # Wait for the page to fully load using Selenium
        try:
            # Adjust the waiting condition to match the unique element on the fully-loaded page
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.p-m-0"))
            )
        except Exception as e:
            self.logger.error(f"Timeout waiting for page to load: {e}")
            return

        # Convert the current Selenium driver page source back to a Scrapy response
        response = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')

        # Extract information from the car page
        carItem = CarItem()
        
        title = response.css("h1.p-m-0::text").get(default=None)
        guarantee = response.css("span.p-border-bottom-dark-gray-3.p-ml-2::text").get(default=None)
        condition = response.css("img.lotIcon.lotIcon-CERT-D::attr(alt)").get(default=None)
        address = response.css("div:contains('ADDRESS') + div span::text").getall()
        phone = response.css("div:contains('PHONE') + div::text").get(default=None)
        sale_date = response.css("span.text-blue font_family_lato_bold p-border-bottom-light-blue p-cursor-pointer p-text-nowrap::text").get(default=None)
        seller_data = response.css("span.p-ml-2 ng-star-inserted::text").get(default=None)

        #______________________Lot datas______________________ 
        lot_details = {}
        lot_info_sections = response.xpath("//div[@class='lot-details-info']")

        for section in lot_info_sections:
            # Extract label (field name) and value
            label = section.xpath(".//label[contains(@class, 'lot-details-label')]/text()").get(default=None)
            value = section.xpath(".//span[contains(@class, 'lot-details-value')]//text()").getall()
            value = " ".join(value).strip()  # Combine and clean value texts

            if label and value:
                lot_details[label.strip().rstrip(":")] = value
        #______________________Lot datas______________________ 

        price = response.css("h1.p-mt-0 amount bidding-heading p-d-inline-block p-position-relative separate-currency-symbol ng-star-inserted::text").get(default=None)
        autocheck = response.css("strong.ldt5-blue-text ng-star-inserted::text").get(default=None)

        self.logger.info(f"Scraped Title: {title}")

        # Check if lot_details contains the keys before accessing them to avoid KeyErrors
        lot_number = lot_details.get("Lot Number", None)
        odometer = lot_details.get("Odometer", None)
        transmission = lot_details.get("Transmission", None)
        drive = lot_details.get("Drive", None)
        fuel = lot_details.get("Fuel", None)
        keys = lot_details.get("Keys", None)

        carItem["url"] = response.url
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

        yield carItem
        time.sleep(60)