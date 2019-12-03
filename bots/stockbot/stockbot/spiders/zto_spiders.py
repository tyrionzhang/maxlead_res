# -*- coding: utf-8 -*-
import scrapy,os,math
from datetime import *
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import spiders_send_email,warehouse_threshold_msgs,warehouse_date_data

class ZtoSpider(scrapy.Spider):
    name = "zto_spider"

    msg_str1 = "complete\n"
    start_urls = [
        'https://fba3-us.zto.cn/stock'
    ]
    sku_list = []
    log_id = None

    def __init__(self, log_id=None, *args, **kwargs):
        super(ZtoSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def parse(self, response):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH)
        driver.get(response.url)
        time.sleep(5)
        elem_name = driver.find_elements_by_name('username')
        elem_pass = driver.find_elements_by_name('password')
        btn_login = driver.find_elements_by_id('sub-btn')

        if elem_name:
            elem_name[0].send_keys('ZTLO')
        if elem_pass:
            elem_pass[0].send_keys('zto5012us')
        btn_login[0].click()
        driver.implicitly_wait(100)
        time.sleep(3)
        stock_li = driver.find_element_by_id('stock')
        stock_li.click()
        driver.implicitly_wait(100)
        time.sleep(3)
        total_count = driver.find_element_by_class_name('el-pagination__total').text
        total_page = int(total_count.split(' ')[1].replace(',','')) / 10
        total_page = math.ceil(total_page)

        old_list_qty = warehouse_date_data(['ZTO'])
        new_qtys = {}
        for i in range(total_page):
            try:
                res = driver.find_elements_by_css_selector('.el-table tbody>tr')
                for val in res:
                    try:
                        item = WarehouseStocksItem()
                        td_re = val.find_elements_by_tag_name('td')
                        if td_re:
                            item['sku'] = td_re[1].text
                            item['warehouse'] = 'ZTO'
                            item['is_new'] = 0
                            if td_re[4].text and not td_re[4].text == ' ':
                                qty5 = int(td_re[5].text)
                                item['qty'] = td_re[4].text
                                item['qty'] = item['qty'].replace(',','')
                                if qty5:
                                    item['qty'] = int(item['qty']) - qty5
                            else:
                                item['qty'] = 0
                            item['qty1'] = 0
                            if old_list_qty:
                                key1 = item['warehouse'] + item['sku']
                                if key1 in old_list_qty:
                                    item['qty1'] = old_list_qty[key1] - int(item['qty'])
                            new_key = item['warehouse'] + item['sku']
                            new_qtys.update({
                                new_key: item['qty']
                            })
                            yield item
                    except IndexError as e:
                        print(e)
                        continue
                if i < total_page - 1:
                    elem_next_page = driver.find_elements_by_class_name('btn-next')
                    if elem_next_page:
                        elem_next_page[0].click()
                        driver.implicitly_wait(100)
                        time.sleep(3)
            except IndexError as e:
                print(e)
                continue
        display.stop()
        driver.quit()
        update_spiders_logs('ZTO', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['ZTO'])
