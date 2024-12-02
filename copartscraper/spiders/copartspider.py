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
import random 

class CopartSpider(scrapy.Spider):
    name = "copartspider"
    start_urls = ["https://www.copart.com/lotSearchResults"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Your-Custom-User-Agent")
        # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        # chrome_options.add_argument("--disable-software-rasterizer")
        # chrome_options.add_argument("--enable-unsafe-swiftshader")

        service = Service(executable_path="chromedriver.exe")  # Update the path to your ChromeDriver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    retry_urls = []
    car_urls = []
    # Use Selenium to navigate and scrape
    def start_requests(self):
        self.driver.get("https://copart.com/lotSearchResults/")

        #  Wait for the table rows to load
        WebDriverWait(self.driver, 60).until(
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
            time.sleep(random.uniform(2, 5))
            car_url = self.car_urls[cars_count]
            
            try:
                self.driver.get(car_url)
                WebDriverWait(self.driver, 120).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.p-m-0"))
                )
                title = self.driver.find_element(By.CSS_SELECTOR, "h1.p-m-0").text
                guarantee = self.driver.find_element(By.CSS_SELECTOR, "span.p-border-bottom-dark-gray-3.p-ml-2").text
                condition_element = self.driver.find_element(By.CSS_SELECTOR, "img.lotIcon.lotIcon-CERT-D")
                condition = condition_element.get_attribute("alt")
                # try: 
                WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@locationinfo='' and contains(@class, 'p-border-bottom-dark-gray-3')]"))
                )
                span_element = self.driver.find_element(By.XPATH, "//span[@locationinfo='' and contains(@class, 'p-border-bottom-dark-gray-3')]")
                span_element.click()

                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'p-mr-4')]"))
                )
                address_container = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-mr-4')]")
                spans = address_container.find_elements(By.XPATH, ".//span")
                address_parts = [span.text.strip() for span in spans if span.text.strip()]
                address = " ".join(address_parts)   
                try:
                    phone_div = self.driver.find_element(By.XPATH, "//div[contains(text(), 'PHONE')]/following-sibling::div")
                    phone = phone_div.text.strip()
                except Exception:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'tel:')]"))
                    )
                    a_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]")
                    # Extract the href attribute value
                    phone_number = a_element.get_attribute("href")
                    # Clean up the phone number (removing 'tel:')
                    if phone_number.startswith("tel:"):
                        phone = phone_number.replace("tel:", "")    
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.text-blue.font_family_lato_bold.p-border-bottom-light-blue"))
                )
                sale_date = self.driver.find_element(By.CSS_SELECTOR, "span.text-blue.font_family_lato_bold.p-border-bottom-light-blue").text
                
                seller_data_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'p-ml-2') and contains(@class, 'ng-star-inserted')]")
                seller_data = seller_data_element.text.strip()

                #______________________Lot datas______________________ 
                lot_details = {}
                lot_info_sections = self.driver.find_elements(By.XPATH, "//div[@class='lot-details-info']")
                    
                for section in lot_info_sections:
                    # Extract label (field name)
                    try:
                        label_element = section.find_element(By.XPATH, ".//label[contains(@class, 'lot-details-label')]")
                        label = label_element.text.strip().rstrip(":")  # Clean up the label text
                    except Exception:
                        label = None

                    # Extract value(s)
                    try:
                        value_elements = section.find_elements(By.XPATH, ".//span[contains(@class, 'lot-details-value')]")
                        values = [value.text.strip() for value in value_elements if value.text.strip()]
                        value = " ".join(values)  # Combine values into a single string
                    except Exception:
                        value = None

                    if label and value:
                        lot_details[label] = value              
            #______________________Lot datas______________________ 
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'amount bidding-heading')]"))
                )
                price_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'amount bidding-heading')]")
                price = price_element.text.strip()
                autocheck_element = self.driver.find_element(By.XPATH, "//strong[contains(@class, 'ldt5-blue-text') and contains(@class, 'ng-star-inserted')]")
                autocheck = autocheck_element.text.strip()
            #     # Check if lot_details contains the keys before accessing them to avoid KeyErrors
                lot_number = lot_details.get("Lot Number")
                odometer = lot_details.get("Odometer")
                transmission = lot_details.get("Transmission")
                drive = lot_details.get("Drive")
                fuel = lot_details.get("Fuel")
                keys = lot_details.get("Keys")
                
                #_____________________________DOP INF___________________________
                try:
                    # Wait for the VIN element to appear
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'VIN') and contains(@class, 'ldt5-list-item')]"))
                    )

                    # Locate the element containing the VIN
                    vin_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'VIN') and contains(@class, 'ldt5-list-item')]")

                    # Extract and clean the VIN text
                    vin_text = vin_element.text.split(":")[-1].strip()
                except Exception as e:
                    # If the VIN element is not found, set vin_text to None
                    vin_text = None
    #_____________________________DOP INF___________________________
                # except Exception as e:  # Use NoSuchElementException for specific handling
                #     self.retry_urls.append(self.driver.current_url)
                #     self.logger.warning(f"Error scraping car {car_url}: {e}")
                #     # Skip the current car and proceed to the next one
                #     time.sleep(30)
                #     cars_count += 1
                #     continue
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
                carItem["price"] = price
                carItem["autocheck"] = autocheck
                carItem["vin_text"] = vin_text
        
                with open('car_data.txt', 'a') as file:
                    # Convert carItem dictionary to a string (JSON format)
                    car_item_str = json.dumps(dict(carItem), ensure_ascii=False, indent=4)
                    file.write(car_item_str + '\n')
                yield carItem
                cars_count += 1

            except Exception:
                self.retry_urls.append(car_url)
                cars_count += 1
