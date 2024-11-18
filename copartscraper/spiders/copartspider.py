import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
                cars_count += 1
                print("**************************CAR_URL:", car_url, "**************************")
                print("Cars count:", cars_count)
                time.sleep(10)
                if car_url:
                    # Yield Scrapy request for each car URL
                    yield scrapy.Request(car_url, callback=self.parse_car_page)
            except Exception as e:
                self.logger.warning(f"Failed to process row: {e}")

        # Close the browser after scraping
        self.driver.quit()

    def parse_car_page(self, response):
        # Extract information from the car page
        print("******************************parse_car_page******************************")
        time.sleep(10)
        with open("current_page.html", "wb") as file:
            file.write(response.body)
        title = response.css("h1.p-m-0::text").get()

        self.logger.info(f"Scraped Title: {title}")
        yield {
            "title": title
            
        }
