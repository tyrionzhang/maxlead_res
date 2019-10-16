# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import Thresholds,SkuUsers,WarehouseStocks
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import spiders_send_email

class Atl1Spider(scrapy.Spider):
    name = "atl1_spider"
    sku_list = []
    msg_str1 = 'complete\n'
    start_urls = [
        'http://us.hipacking.com/member/passport'
    ]

    # def __init__(self, username=None, *args, **kwargs):
    #     super(AtlSpider, self).__init__(*args, **kwargs)
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
        elem_name = driver.find_elements_by_name('uid')
        elem_pass = driver.find_elements_by_name('pwd')
        btn_login = driver.find_elements_by_class_name('btn-success')

        if elem_name:
            elem_name[0].send_keys('tradeforce')
        if elem_pass:
            elem_pass[0].send_keys('1202@hxml')
        btn_login[0].click()
        driver.implicitly_wait(100)
        driver.get('http://us.hipacking.com/member/instock/stock.html')
        driver.implicitly_wait(100)
        total_page = driver.find_elements_by_css_selector('.nav-list-wrapper span:nth-child(2)>b')[0].text
        total_page = int(total_page)
        items = []
        for i in range(total_page):
            try:
                res = driver.find_elements_by_css_selector('.table tbody>tr')
                for val in res:
                    item = WarehouseStocksItem()
                    td_re = val.find_elements_by_tag_name('td')
                    if td_re:
                        item['sku'] = td_re[3].text
                        item['warehouse'] = 'ATL'
                        item['is_new'] = 0
                        if td_re[11].text and not td_re[11].text == ' ':
                            item['qty'] = td_re[11].text
                            item['qty'] = item['qty'].replace(',', '')
                        else:
                            item['qty'] = 0
                        items.append(item)

                if i < (total_page - 1):
                    elem_next_page = 'http://us.hipacking.com/member/instock/stock.html?pageIndex=%s&keyword=&warehouse=&sort=NormalCount' % (i + 2)
                    if elem_next_page:
                        driver.get(elem_next_page)
                        driver.implicitly_wait(100)
            except:
                continue

        display.stop()
        driver.quit()

        for i, val in enumerate(items, 0):
            for n, v in enumerate(items, 0):
                if v['sku'] == val['sku'] and not i == n:
                    val['qty'] = int(v['qty']) + int(val['qty'])
                    del items[n]
            date_now = datetime.now()
            date0 = date_now.strftime('%Y-%m-%d')
            obj = WarehouseStocks.objects.filter(sku=val['sku'], warehouse=val['warehouse'], created__contains=date0)
            date1 = date_now - timedelta(days=1)
            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse=val['warehouse'],
                                                  created__contains=date1.strftime('%Y-%m-%d'))
            if obj1:
                val['qty1'] = obj1[0].qty - int(val['qty'])
            if obj:
                obj.delete()
            yield val

            threshold = Thresholds.objects.filter(sku=val['sku'], warehouse=val['warehouse'])
            user = SkuUsers.objects.filter(sku=val['sku'])
            if threshold and threshold[0].threshold >= int(val['qty']):
                if user:
                    msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (
                        user[0].user.email, val['sku'], val['warehouse'], val['qty'], threshold[0].threshold)

        update_spiders_logs('ATL')

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
