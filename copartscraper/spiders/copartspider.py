import scrapy
import json
import time
import random
from ..items import CarItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CopartSpider(scrapy.Spider):
    name = "copartspider"
    start_urls = ["https://www.copart.com/lotSearchResults"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Selenium Chrome Driver setup
        chrome_options = Options()
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Your-Custom-User-Agent")
        # Uncomment the below line for headless mode if needed
        # chrome_options.add_argument("--headless")
        
        service = Service(executable_path="chromedriver.exe")  # Update the path
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument", 
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        self.retry_urls = []
        self.retry_auctions = []
        self.car_urls = []
        self.auctions = []
        self.cars_count = 0
        self.auctions_count = 0

    def start_requests(self):
        self.driver.get("https://copart.com/auctionCalendar/")
        
        # Wait for reCAPTCHA if present
        self.wait_for_recaptcha()
        # time.sleep(30)
        # Wait for the table to load
        WebDriverWait(self.driver, 90).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@data-uname='auctionscalenderTable']"))
        )

        # Locate the table element
        table = self.driver.find_element(By.XPATH, "//table[@data-uname='auctionscalenderTable']")
        a_elements = table.find_elements(By.TAG_NAME, "a")

        # Extract all auction URLs
        for a in a_elements:
            href = a.get_attribute("href")
            self.auctions.append(href)

        # Parse each auction page
        while self.auctions_count < len(self.auctions):
            self.parse_auction_pages(self.auctions[self.auctions_count])
            while self.cars_count < len(self.car_urls):
                yield scrapy.Request(
                        url=self.car_urls[self.cars_count],
                        callback=self.parse_car_page,
                        meta={"car_url": self.car_urls[self.cars_count]},
                    )
                self.cars_count += 1
            self.auctions_count += 1

    def wait_for_recaptcha(self):
        """Waits for manual reCAPTCHA solving."""
        self.logger.info("Please solve reCAPTCHA manually. If there is no reCAPTCHA just press Enter.")
        input("Press Enter after solving the reCAPTCHA...")

    def parse_auction_pages(self, auction_url):
        """Navigate through all auction pages."""
        # for auction_url in self.auctions:
        last_page_check = True
        try:
            self.driver.get(auction_url)
            while last_page_check:
                ##### time.sleep(5)
                WebDriverWait(self.driver, 300).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
                )
                
                table = self.driver.find_element(By.CSS_SELECTOR, "table")
                body = table.find_element(By.CSS_SELECTOR, "tbody")
                rows = body.find_elements(By.CSS_SELECTOR, "tr")
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
                )
                for row in rows:
                    car_link = row.find_element(By.TAG_NAME, "a").get_attribute("href")
                    if car_link:
                        self.car_urls.append(car_link)
                    # except Exception as e:
                    #     self.logger.warning(f"Failed to extract car link: {e}")
                ##### time.sleep(random.uniform(2, 5))
                # try:
                # Wait for the next button to be clickable
                try:
    # Wait for the button to be clickable
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.p-paginator-next"))
                    )
                    
                    # Click the button
                    next_button.click()
                except Exception as e:
                    last_page_check = False
                    time.sleep(30)
        except Exception as e:
            self.logger.error(f"Failed to process auction page {auction_url}: {e}")
            # time.sleep(30)
            self.retry_auctions.append(auction_url)
        
        # Parse car pages after gathering all URLs
    #________________________________________________________________________________________________________________
    
    def parse_car_page(self, response):
        car_url = response.meta.get("car_url")
        ##### time.sleep(random.uniform(2, 5))
        # try:
        self.driver.get(car_url)
        WebDriverWait(self.driver, 120).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "h1").text
        except Exception:
            title = "N/A"
        # guarantee = self.driver.find_element(By.CSS_SELECTOR, "span.p-border-bottom-dark-gray-3.p-ml-2").text
#         condition_element = self.driver.find_element(By.CSS_SELECTOR, "img.lotIcon.lotIcon-CERT-D")
#         condition = condition_element.get_attribute("alt")
#         # try: 
#         WebDriverWait(self.driver, 20).until(
#             EC.element_to_be_clickable((By.XPATH, "//span[@locationinfo='' and contains(@class, 'p-border-bottom-dark-gray-3')]"))
#         )
#         span_element = self.driver.find_element(By.XPATH, "//span[@locationinfo='' and contains(@class, 'p-border-bottom-dark-gray-3')]")
#         span_element.click()

#         WebDriverWait(self.driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'p-mr-4')]"))
#         )
#         address_container = self.driver.find_element(By.XPATH, "//div[contains(@class, 'p-mr-4')]")
#         spans = address_container.find_elements(By.XPATH, ".//span")
#         address_parts = [span.text.strip() for span in spans if span.text.strip()]
#         address = " ".join(address_parts)   
#         try:
#             phone_div = self.driver.find_element(By.XPATH, "//div[contains(text(), 'PHONE')]/following-sibling::div")
#             phone = phone_div.text.strip()
#         except Exception:
#             WebDriverWait(self.driver, 20).until(
#                 EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'tel:')]"))
#             )
#             a_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]")
#             # Extract the href attribute value
#             phone_number = a_element.get_attribute("href")
#             # Clean up the phone number (removing 'tel:')
#             if phone_number.startswith("tel:"):
#                 phone = phone_number.replace("tel:", "")
#         WebDriverWait(self.driver, 20).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "span.text-blue.font_family_lato_bold.p-border-bottom-light-blue"))
#         )
#         sale_date = self.driver.find_element(By.CSS_SELECTOR, "span.text-blue.font_family_lato_bold.p-border-bottom-light-blue").text
        
#         seller_data_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'p-ml-2') and contains(@class, 'ng-star-inserted')]")
#         seller_data = seller_data_element.text.strip()

        #______________________Lot datas______________________ 
        # Dictionary to store lot details
        lot_details = {}

        try:
            # Wait for the panel-content div to load
            panel = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".panel-content"))
            )

            # Find all field containers within the panel (assuming consistent structure)

            field_containers = panel.find_elements(By.CSS_SELECTOR, "div.d-flex.border-top-gray")

            lot_element = panel.find_element(By.CSS_SELECTOR, ".lot-details-desc")
            lot_text = lot_element.text.strip()
            lot_details['Lot Number'] = lot_text
            # Loop through each container to extract labels and spans
            for container in field_containers:
                # Find the label
                label_element = container.find_element(By.TAG_NAME, "label")
                label_text = label_element.text.strip().replace(":", "")  # Remove colon for clean key

                # Find the corresponding span or value
                try:
                    span_element = container.find_element(By.CSS_SELECTOR, ".lot-details-desc")
                    value_text = span_element.text.strip()
                except Exception:
                    value_text = "N/A"  # If no span is found, set value as "N/A"

                # Add to dictionary
                lot_details[label_text] = value_text

        except Exception as e:
            print(f"Error extracting lot details: {e}")

        # Print all lot details
        for key, value in lot_details.items():
            print("**************************************", f"{key}: {value}", "**************************************")
             
#     #______________________Lot datas______________________ 
#         WebDriverWait(self.driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'amount bidding-heading')]"))
#         )
        price_element = self.driver.find_element(By.CSS_SELECTOR, "span.bid-price")
        price = price_element.text.strip().replace("$", "")
#         autocheck_element = self.driver.find_element(By.XPATH, "//strong[contains(@class, 'ldt5-blue-text') and contains(@class, 'ng-star-inserted')]")
#         autocheck = autocheck_element.text.strip()
        # Check if lot_details contains the keys before accessing them to avoid KeyErrors
        lot_number = lot_details.get("Lot Number")
        odometer = lot_details.get("Odometer")
        title_code = lot_details.get("Title Code")
        drive = lot_details.get("Drive")
        fuel = lot_details.get("Fuel")
        keys = lot_details.get("Keys")
        transmission = lot_details.get("Transmission")
        VIN = lot_details.get("VIN")
        primary_damage = lot_details.get("Primary Damage")
        secondary_damage = lot_details.get("Secondary Damage")
        ERV = lot_details.get("Estimated Retail Value")
        cylinders = lot_details.get("Cylinders")
        body_style = lot_details.get("Body Style")
        color = lot_details.get("Color")
        engine_type = lot_details.get("Engine Type")
        vehicle_type = lot_details.get("Vehicle Type")
        highlights = lot_details.get("Highlights")
        notes = lot_details.get("Notes")
        
        
#         #_____________________________DOP INF___________________________
#         try:
#             # Wait for the VIN element to appear
#             WebDriverWait(self.driver, 20).until(
#                 EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'VIN') and contains(@class, 'ldt5-list-item')]"))
#             )

#             # Locate the element containing the VIN
#             vin_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'VIN') and contains(@class, 'ldt5-list-item')]")

#             # Extract and clean the VIN text
#             vin_text = vin_element.text.split(":")[-1].strip()
#         except Exception as e:
#             # If the VIN element is not found, set vin_text to None
#             vin_text = None
# #_____________________________DOP INF___________________________
#         # except Exception as e:  # Use NoSuchElementException for specific handling
#         #     self.retry_urls.append(self.driver.current_url)
#         #     self.logger.warning(f"Error scraping car {car_url}: {e}")
#         #     # Skip the current car and proceed to the next one
#         #     time.sleep(30)
#         #     cars_count += 1
#         #     continue
#         self.logger.info(f"Scraped Title: {title}")
        carItem = CarItem()
#         print("******************************************************************")
#         time.sleep(30)
        
        # Safe extraction with validation
        carItem["url"] = car_url
        carItem["title"] = title if title else "N/A"
#         carItem["guarantee"] = guarantee if guarantee else "N/A"
#         carItem["condition"] = condition if condition else "Unknown"
#         carItem["address"] = address if address else "N/A"
#         carItem["phone"] = phone if phone else "N/A"
#         carItem["sale_date"] = sale_date if sale_date else "N/A"
#         carItem["seller_data"] = seller_data if seller_data else "N/A"
        carItem["lot_number"] = lot_number if lot_number else "N/A"
        carItem["odometer"] = odometer if odometer else "N/A"
        carItem["title_code"] = title_code if title_code else "N/A"
        carItem["drive"] = drive if drive else "N/A"
        carItem["fuel"] = fuel if fuel else "N/A"
        carItem["keys"] = keys if keys else "Unknown"
        carItem["price"] = price if price else "0"
#         carItem["autocheck"] = autocheck if autocheck else "Not Available"
#         carItem["vin_text"] = vin_text if vin_text else "N/A"
        
        carItem["transmission"] = transmission
        carItem["VIN"] = VIN
        carItem["primary_damage"] = primary_damage
        carItem["secondary_damage"] = secondary_damage
        carItem["ERV"] = ERV
        carItem["cylinders"] = cylinders
        carItem["body_style"] = body_style
        carItem["color"] = color
        carItem["engine_type"] = engine_type
        carItem["vehicle_type"] = vehicle_type
        carItem["highlights"] = highlights
        carItem["notes"] = notes

        with open('car_data.txt', 'a') as file:
            # Convert carItem dictionary to a string (JSON format)
            car_item_str = json.dumps(dict(carItem), ensure_ascii=False, indent=4)
            file.write(car_item_str + '\n')
        yield carItem
        # except Exception:
        #     self.retry_urls.append(car_url)
        #     self.cars_count += 1
