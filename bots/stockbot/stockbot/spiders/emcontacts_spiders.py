# -*- coding: utf-8 -*-
import scrapy,math,time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import OrderItemsItem
from max_stock.models import AmazonCode
from django.core.mail import send_mail

class EmcontactsSpider(scrapy.Spider):
    name = "emcontacts_spider"

    start_urls = ['https://accounts.google.com/ServiceLogin?passive=1209600&osid=1&continue=https://contacts.google.com/?hl%3Dzh-CN&followup=https://contacts.google.com/?hl%3Dzh-CN&hl=zh-CN']
    next_url = ''

    def parse(self, response):
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        chrome_options = Options()
        chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(response.url)
        elem_email = driver.find_elements_by_id('Email')
        btn_login = driver.find_elements_by_id('next')
        if elem_email:
            elem_email[0].send_keys('maxlead.us@gmail.com')
        btn_login[0].click()
        driver.implicitly_wait(100)
        elem_pass = driver.find_elements_by_id('Passwd')
        btn_pass = driver.find_elements_by_id('signIn')
        if elem_pass:
            elem_pass[0].send_keys('ljyypswmfjyjhryp')
        btn_pass[0].click()
        driver.implicitly_wait(100)
        btn_pass = driver.find_elements_by_id('passwordNext')
        print(btn_pass[0].text)
        pass
        driver.quit()