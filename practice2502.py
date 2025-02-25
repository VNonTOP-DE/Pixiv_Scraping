import scrapy
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PixivSpider(scrapy.Spider):
    name = 'pixiv_spider'
    start_urls = ['https://www.pixiv.net/en/artworks/62492065']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'COOKIES_ENABLED': True,
    }

    def __init__(self):
        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode (no browser window)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.custom_settings["USER_AGENT"]}')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def parse(self, response):
        logger.info(f"Parsing URL: {response.url}")
        
        # Use Selenium to load the page
        self.driver.get(response.url)
        # Wait for the recommendation section to load (adjust timeout as needed)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gtm-illust-recommend-zone'))
            )
        except Exception as e:
            logger.warning(f"Recommendation section not found after timeout: {e}")
            logger.debug(f"Page source preview: {self.driver.page_source[:500]}")
            return

        # Parse the rendered page with Scrapy
        response = scrapy.http.TextResponse(
            url=response.url,
            body=self.driver.page_source.encode('utf-8'),
            encoding='utf-8'
        )

        # Target the recommendation zone
        artwork_links = response.css('div.gtm-illust-recommend-zone a.sc-d98f2c-0.sc-rp5asc-16.iUsZyY')
        logger.info(f"Found {len(artwork_links)} artwork links")
        
        if not artwork_links:
            logger.warning("No artwork links found.")
            logger.debug(f"Response body preview: {response.text[:500]}")
        
        # Write IDs to file
        with open('pixiv_ids.txt', 'a', encoding='utf-8') as f:
            for link in artwork_links:
                artwork_id = link.css('::attr(data-gtm-recommend-illust-id)').get()
                if artwork_id:
                    logger.info(f"Found artwork ID: {artwork_id}")
                    f.write(f"{artwork_id}\n")
                else:
                    logger.warning("No artwork ID found in link")
        
        # Follow related artwork links
        related_links = response.css('a[href*="/en/artworks/"]::attr(href)').getall()
        logger.info(f"Found {len(related_links)} related links")
        for link in related_links:
            if link not in self.start_urls:
                logger.info(f"Following link: {link}")
                yield response.follow(link, callback=self.parse)

    def closed(self, reason):
        # Clean up: close the browser when the spider finishes
        self.driver.quit()
        logger.info("Browser closed.")

def main():
    process = CrawlerProcess()
    process.crawl(PixivSpider)
    process.start()

if __name__ == "__main__":
    main()