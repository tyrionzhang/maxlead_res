# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import xlrd
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import warehouse_threshold_msgs,warehouse_date_data

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
        profile = webdriver.FirefoxProfile()
        down_path = os.path.join(settings.DOWNLOAD_DIR, 'zto_tb')
        profile.set_preference('browser.download.dir', down_path)  # 现在文件存放的目录
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, '
                               'text/csv,application/x-msexcel,application/x-excel,application/excel,application/vnd.ms-excel,application/x-download')
        # profile.set_preference("permissions.default.image", 2)
        # profile.set_preference("network.http.use-cache", False)
        # profile.set_preference("browser.cache.memory.enable", False)
        # profile.set_preference("browser.cache.disk.enable", False)
        # profile.set_preference("browser.sessionhistory.max_total_viewers", 3)
        # profile.set_preference("network.dns.disableIPv6", True)
        # profile.set_preference("Content.notify.interval", 750000)
        # profile.set_preference("content.notify.backoffcount", 3)
        # profile.set_preference("network.http.pipelining", True)
        # profile.set_preference("network.http.proxy.pipelining", True)
        # profile.set_preference("network.http.pipelining.maxrequests", 32)

        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)
        driver.get(response.url)
        time.sleep(5)
        btn_export = False
        files = False
        new_qtys = {}
        try:
            elem_name = driver.find_elements_by_name('username')
            elem_pass = driver.find_elements_by_name('password')
            btn_login = driver.find_element_by_id('sub-btn')

            if elem_name:
                elem_name[0].send_keys('ZTLO')
            if elem_pass:
                elem_pass[0].send_keys('zto5012us')
            btn_login.click()
            driver.implicitly_wait(100)
            time.sleep(3)
            try:
                wrapper_btn = driver.find_elements_by_class_name('el-button--small')
                if wrapper_btn and wrapper_btn[1].is_displayed():
                    wrapper_btn[1].click()
            except:
                pass
            stock_li = driver.find_element_by_id('stock')
            stock_li.click()
            driver.implicitly_wait(100)
            time.sleep(3)
            waits = 0
            while 1:
                time.sleep(3)
                try:
                    btn_export = driver.find_element_by_css_selector('.text-right>button:nth-of-type(2)')
                    break
                except:
                    waits += 5
                    if waits > 120:
                        break
                    continue
            if btn_export:
                btn_export.click()
                time.sleep(20)
                old_list_qty = warehouse_date_data(['ZTO'])
                files = os.listdir(down_path)
                if files:
                    f_path = os.path.join(down_path, files[0])
                    if os.path.isfile(f_path):
                        data = xlrd.open_workbook(f_path)  # 打开fname文件
                        data.sheet_names()  # 获取xls文件中所有sheet的名称
                        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
                        nrows = table.nrows
                        for i in range(1, nrows):
                            try:
                                if i >= nrows:
                                    break
                                item = WarehouseStocksItem()
                                item['sku'] = table.cell_value(i, 1, )
                                item['warehouse'] = 'ZTO'
                                item['is_new'] = 0
                                qty = table.cell_value(i, 3, )
                                if qty:
                                    qty5 = int(table.cell_value(i, 5, ))
                                    item['qty'] = qty
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
                            except:
                                continue
        except:
            pass
        try:
            driver.refresh()
            driver.switch_to.alert.accept()
            driver.implicitly_wait(100)
        except:
            pass
        shutil.rmtree(down_path)
        os.mkdir(down_path)
        display.stop()
        driver.quit()
        if files:
            update_spiders_logs('ZTO', log_id=self.log_id)
            msg_str2 = warehouse_threshold_msgs(new_qtys, ['ZTO'])
