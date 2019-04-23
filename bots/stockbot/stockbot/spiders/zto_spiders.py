# -*- coding: utf-8 -*-
import scrapy,os,math
from datetime import *
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from maxlead_site.common.common import spiders_send_email

class ZtoSpider(scrapy.Spider):
    name = "zto_spider"

    msg_str1 = "complete\n"
    start_urls = [
        'https://fba3-us.zto.cn/stock'
    ]
    sku_list = []

    # def __init__(self, username=None, *args, **kwargs):
    #     super(HanoverSpider, self).__init__(*args, **kwargs)
    #     file_name = 'userSkus_txt.txt'
    #     if username:
    #         file_name = 'userSkus_txt_%s.txt' % username
    #     file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, file_name)
    #     with open(file_path, "r") as f:
    #         sku_list = f.read()
    #         f.close()
    #     if sku_list:
    #         self.sku_list = eval(sku_list)

    def parse(self, response):
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
        msg_str2 = ''
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
            elem_pass[0].send_keys('usZTO5012')
        btn_login[0].click()
        driver.implicitly_wait(100)
        stock_li = driver.find_element_by_id('stock')
        time.sleep(3)
        stock_li.click()
        driver.implicitly_wait(100)
        time.sleep(3)
        total_count = driver.find_element_by_class_name('el-pagination__total').text
        total_page = int(total_count.split(' ')[1].replace(',','')) / 10
        total_page = math.ceil(total_page)
        for i in range(total_page):
             try:
                res = driver.find_elements_by_css_selector('.el-table tbody>tr')
                for val in res:
                    item = WarehouseStocksItem()
                    td_re = val.find_elements_by_tag_name('td')
                    if td_re:
                        item['sku'] = td_re[1].text
                        item['warehouse'] = 'ZTO'
                        item['is_new'] = 0
                        if td_re[4].text and not td_re[4].text == ' ':
                            item['qty'] = td_re[4].text
                            item['qty'] = item['qty'].replace(',','')
                        else:
                            item['qty'] = 0
                        date_now = datetime.now()
                        date0 = date_now.strftime('%Y-%m-%d')
                        obj = WarehouseStocks.objects.filter(sku=item['sku'], warehouse=item['warehouse'],
                                                             created__contains=date0)
                        date1 = date_now - timedelta(days=1)
                        obj1 = WarehouseStocks.objects.filter(sku=item['sku'], warehouse=item['warehouse'],
                                                              created__contains=date1.strftime('%Y-%m-%d'))
                        if obj1:
                            item['qty1'] = obj1[0].qty - int(item['qty'])
                        if obj:
                            obj.delete()
                        yield item

                        threshold = Thresholds.objects.filter(sku=item['sku'], warehouse=item['warehouse'])
                        user = SkuUsers.objects.filter(sku=item['sku'])
                        if threshold and threshold[0].threshold >= int(item['qty']):
                            if user:
                                msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % ( user[0].user.email,
                                                        item['sku'], item['warehouse'], item['qty'], threshold[0].threshold)
                if i < total_page - 1:
                    elem_next_page = driver.find_elements_by_class_name('btn-next')
                    if elem_next_page:
                        time.sleep(3)
                        elem_next_page[0].click()
                        driver.implicitly_wait(100)
                        time.sleep(3)
             except IndexError as e:
                 print(e)
                 continue
        display.stop()
        driver.quit()

        if not os.path.isfile(file_path):
            with open(file_path, "w+") as f:
                f.close()
        with open(file_path, "r+") as f:
            old = f.read()
            f.seek(0)
            f.write(self.msg_str1)
            f.write(old)
            f.write(msg_str2)
            f.close()

        with open(file_path, "r") as f:
            msg1 = f.readline()
            msg2 = f.readline()
            msg3 = f.readline()
            msg4 = f.readline()
            msg5 = f.readline()
            if msg1 == 'complete\n' and msg2 == 'complete\n' and msg3 == 'complete\n' and msg4 == 'complete\n' and msg5 == 'complete\n':
                spiders_send_email(f, file_path=file_path)

