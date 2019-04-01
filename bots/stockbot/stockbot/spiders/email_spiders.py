# -*- coding: utf-8 -*-
import scrapy,math,time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import OrderItemsItem
from max_stock.models import AmazonCode
from django.core.mail import send_mail

class EmailSpider(scrapy.Spider):
    name = "email_spider"

    # start_urls = ['https://docs.google.com/spreadsheets/d/1cIW9ksnTu-k0G2_bMYno56j7lep2IDdz7jsH_wQZMvw/edit#gid=0']
    start_urls = ['https://sellercentral.amazon.com/gp/homepage.html/ref=asus_login_hnav']
    next_url = ''

    def parse(self, response):
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        chrome_options = Options()
        # chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=chrome_options, executable_path=settings.FIREFOX_PATH,
                                  service_log_path=settings.LOG_PATH)
        driver.get(response.url)
        elem_email = driver.find_elements_by_id('ap_email')
        elem_pass = driver.find_elements_by_id('ap_password')
        btn_login = driver.find_elements_by_id('signInSubmit')
        if elem_email:
            elem_email[0].send_keys('rudy.zhangwei@cdsht.cn')
        if elem_pass:
            elem_pass[0].send_keys('mc123456')
        btn_login[0].click()
        time.sleep(200)
        code = ''
        code_obj = AmazonCode.objects.filter(email='rudy.zhangwei@cdsht.cn')
        if code_obj:
            code = code_obj[0].code
        code_obj.delete()
        elem_code = driver.find_elements_by_id('auth-mfa-otpcode')
        btn_code_login = driver.find_elements_by_id('auth-signin-button')
        remembers = driver.find_elements_by_id('auth-mfa-remember-device')
        if remembers:
            remembers[0].click()
            driver.implicitly_wait(100)
        if elem_code:
            elem_code[0].send_keys(code)
            btn_code_login[0].click()
            driver.implicitly_wait(100)

        elem_order = driver.find_elements_by_css_selector('#sc-top-nav-root a.sc-menu-trigger')
        if elem_order:
            driver.get('https://sellercentral.amazon.com/gp/orders-v2/list/ref=ag_myo_tnav_xx_')
            driver.implicitly_wait(100)
            selc_date = Select(driver.find_element_by_id('_myoLO_preSelectedRangeSelect'))
            selc_date.select_by_value('1')
            btn_search = driver.find_element_by_id('SearchID')
            btn_search.click()
            driver.implicitly_wait(30)
            time.sleep(30)

        order_trs = driver.find_elements_by_css_selector('#myo-table>table>tbody>tr')
        page_el = order_trs[-2].find_elements_by_css_selector('td tr>td:nth-child(1) strong:last-child')
        total_page = 0
        if page_el:
            counts = page_el[0].text
            total_page = math.ceil(int(counts) / 15)
        for n in range(0, total_page):
            if self.next_url:
                driver.get(self.next_url)
                driver.implicitly_wait(30)
            order_trs = driver.find_elements_by_css_selector('#myo-table>table>tbody>tr.order-row')
            length = len(order_trs)
            for i in range(0, length):
                item = OrderItemsItem()
                if not i == 0:
                    driver.back()
                    driver.implicitly_wait(30)
                    time.sleep(10)
                order_trs = driver.find_elements_by_css_selector('#myo-table>table>tbody>tr.order-row')
                item['order_id'] = order_trs[i].get_attribute('id').replace('row-', '')
                elem_sku = order_trs[i].find_elements_by_css_selector('td:nth-child(3) table>tbody>tr:nth-child(2)>td:nth-child(3)>span:nth-child(2)')
                if elem_sku:
                    item['sku'] = elem_sku[0].text
                elem_status = order_trs[i].find_elements_by_css_selector('td:nth-child(5)>div:nth-child(2)')
                if elem_status:
                    item['order_status'] = elem_status[0].text
                email_el = order_trs[i].find_elements_by_css_selector(
                    'td:nth-child(3)>div:nth-child(3)>div:nth-child(1)>a')
                if not email_el:
                    email_el = order_trs[i].find_elements_by_css_selector(
                        'td:nth-child(3)>div:nth-child(4)>div:nth-child(1)>a')
                if email_el:
                    email_el[0].click()
                toformbox = driver.find_elements_by_css_selector('#toFromBox>div:nth-child(1) .tiny')
                if toformbox:
                    item['email'] = toformbox[0].text.replace('(', '')
                    item['email'] = item['email'].replace(')', '')
                if item:
                    yield item
            driver.back()
            driver.implicitly_wait(30)
            time.sleep(10)
            order_trs = driver.find_elements_by_css_selector('#myo-table>table>tbody>tr')
            last_link_el = order_trs[-2].find_elements_by_css_selector('td tr>td:nth-child(3) a:last-child')
            if last_link_el:
                self.next_url = last_link_el[0].get_attribute('href')
        # display.stop()
        driver.quit()
