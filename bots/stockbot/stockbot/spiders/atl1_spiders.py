# -*- coding: utf-8 -*-
import scrapy,time
from django.db import connection
from django.db.utils import OperationalError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import warehouse_date_data,warehouse_threshold_msgs

class Atl1Spider(scrapy.Spider):
    name = "atl1_spider"
    sku_list = []
    msg_str1 = 'complete\n'
    start_urls = [
        'http://us.hipacking.com/member/passport'
    ]
    log_id = None

    def __init__(self, log_id=None, *args, **kwargs):
        super(Atl1Spider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def parse(self, response):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
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
                        w_name = td_re[1].text
                        if w_name == 'ONT-2':
                            item['warehouse'] = 'ONT'
                        elif w_name == 'KCM-4':
                            item['warehouse'] = 'KCM'
                        else:
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
                        driver.refresh()
                        driver.switch_to.alert.accept()
                        driver.implicitly_wait(100)
                        time.sleep(3)
            except:
                continue

        display.stop()
        driver.quit()

        querysetlist = []
        old_list_qty = warehouse_date_data(['ATL', 'ONT', 'KCM'])
        new_qtys = {}
        for i, val in enumerate(items, 0):
            try:
                for n, v in enumerate(items, 0):
                    if v['sku'] == val['sku'] and not i == n and  val['warehouse'] == v['warehouse']:
                        val['qty'] = int(v['qty']) + int(val['qty'])
                        del items[n]
                val['qty1'] = 0
                if old_list_qty:
                    key1 = val['warehouse'] + val['sku']
                    if key1 in old_list_qty:
                        val['qty1'] = old_list_qty[key1] - int(val['qty'])

                querysetlist.append(WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))

                new_key = val['warehouse'] + val['sku']
                new_qtys.update({
                    new_key: val['qty']
                })
            except OperationalError:
                connection.cursor()
                connection.close()
                continue

        WarehouseStocks.objects.bulk_create(querysetlist)
        update_spiders_logs('ATL', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['ATL', 'ONT', 'KCM'])
