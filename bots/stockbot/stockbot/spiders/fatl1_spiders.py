# -*- coding: utf-8 -*-
import scrapy,os
import csv
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from max_stock.models import FbaTransportTask

class Fatl1Spider(scrapy.Spider):
    name = "fatl1_spider"
    start_urls = [
        'https://www.amazon.com/gp/bestsellers/home-garden/3733721/ref=pd_zg_hrsr_home-garden',
        'https://www.amazon.com/gp/bestsellers/hi/6808092011/ref=pd_zg_hrsr_hi',
        'https://www.amazon.com/gp/bestsellers/baby-products/166846011/ref=pd_zg_hrsr_baby-products',
        'https://www.amazon.com/gp/bestsellers/baby-products/166809011/ref=pd_zg_hrsr_baby-products',
        'https://www.amazon.com/gp/bestsellers/lawn-garden/2475557011/ref=pd_zg_hrsr_lawn-garden',
        'https://www.amazon.com/Best-Sellers-Garden-Outdoor-Swimming-Pools/zgbs/lawn-garden/166442011/ref=zg_bs_nav_lg_2_1272941011',
        'https://www.amazon.com/Best-Sellers-Garden-Outdoor-Heating-Cooling/zgbs/lawn-garden/13638732011/ref=zg_bs_nav_lg_1_lg',
        'https://www.amazon.com/Best-Sellers-Garden-Outdoor-Gardening-Lawn-Care/zgbs/lawn-garden/3610851/ref=zg_bs_nav_lg_1_lg',
        'https://www.amazon.com/Best-Sellers-Garden-Outdoor-Firewood-Racks/zgbs/lawn-garden/3563995011/ref=zg_bs_nav_lg_2_13638732011',
        'https://www.amazon.com/Best-Sellers-Garden-Outdoor-Pond-Equipment/zgbs/lawn-garden/13764241/ref=zg_bs_nav_lg_3_3563987011',
        'https://www.amazon.com/Best-Sellers-Baby-Travel-Gear/zgbs/baby-products/17726796011/ref=zg_bs_nav_ba_1_ba',
        'https://www.amazon.com/Best-Sellers-Baby-Nursery-Bedding-Mattresses/zgbs/baby-products/11625834011/ref=zg_bs_nav_ba_2_695338011',
        'https://www.amazon.com/Best-Sellers-Baby-Portable-Changing-Pads/zgbs/baby-products/2237474011/ref=zg_bs_nav_ba_2_17726796011',
        'https://www.amazon.com/Best-Sellers-Baby-Nursery-Furniture/zgbs/baby-products/166809011/ref=zg_bs_nav_ba_2_695338011',
        'https://www.amazon.com/Best-Sellers-Baby-Infant-Toddler-Beds/zgbs/baby-products/166812011/ref=zg_bs_nav_ba_3_166809011',
        'https://www.amazon.com/Best-Sellers-Baby-Glider-Chairs-Ottomans-Rocking/zgbs/baby-products/239222011/ref=zg_bs_nav_ba_3_166809011',
        'https://www.amazon.com/Best-Sellers-Baby-Playards/zgbs/baby-products/166841011/ref=zg_bs_nav_ba_3_166809011',
        'https://www.amazon.com/Best-Sellers-Baby-Nursery-Storage-Organization-Products/zgbs/baby-products/3744921/ref=zg_bs_nav_ba_3_166809011'
    ]

    def __init__(self, xlsx_file=None, *args, **kwargs):
        super(Fatl1Spider, self).__init__(*args, **kwargs)
        if xlsx_file:
            self.xlsx_file = xlsx_file

    def parse(self, response):
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("permissions.default.image", 2)
        profile.set_preference("network.http.use-cache", False)
        profile.set_preference("browser.cache.memory.enable", False)
        profile.set_preference("browser.cache.disk.enable", False)
        profile.set_preference("browser.sessionhistory.max_total_viewers", 3)
        profile.set_preference("network.dns.disableIPv6", True)
        profile.set_preference("Content.notify.interval", 750000)
        profile.set_preference("content.notify.backoffcount", 3)
        profile.set_preference("network.http.pipelining", True)
        profile.set_preference("network.http.proxy.pipelining", True)
        profile.set_preference("network.http.pipelining.maxrequests", 32)

        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)

        listing_items = []
        page_first = self.get_top_page(driver, response.url)
        listing_urls = page_first['listing_urls']
        if page_first['last_page_url']:
            page_se = self.get_top_page(driver, page_first['last_page_url'])
            listing_urls = listing_urls + page_se['listing_urls']

        for url in listing_urls:
            retry_count = 0
            while True:
                try:
                    driver.get(url)
                    driver.implicitly_wait(100)
                    title = driver.find_element_by_id('productTitle').text
                    listing_items.append([title])
                    break
                except:
                    retry_count += 1
                    if retry_count > 3:
                        break
                    try:
                        driver.close()
                    except:
                        pass
                    driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH,
                                               firefox_profile=profile)

        if listing_items:
            down_path = os.path.join(settings.DOWNLOAD_DIR, 'test.csv')
            with open(down_path, "a+", encoding='utf-8', newline='') as file:  # 处理csv读写时不同换行符  linux:\n    windows:\r\n    mac:\r
                csv_file = csv.writer(file)
                csv_file.writerows(listing_items)
                file.close()
        try:
            # display.stop()
            driver.close()
        except:
            pass

    def get_top_page(self, driver, url):
        listing_urls = []
        retry = 0
        last_page_url = ''
        while True:
            try:
                driver.get(url)
                driver.implicitly_wait(100)
                listings = driver.find_elements_by_class_name('zg-item-immersion')
                last_page_url = driver.find_elements_by_css_selector('.a-last a')
                for val in listings:
                    listing_urls.append(val.find_element_by_class_name('a-link-normal').get_attribute('href'))
                break
            except:
                retry += 1
                if retry > 3:
                    break

        if last_page_url:
            last_page_url = last_page_url[0].get_attribute('href')
        return {
            'listing_urls' : listing_urls,
            'last_page_url' : last_page_url
        }