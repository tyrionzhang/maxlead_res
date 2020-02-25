# -*- coding: utf-8 -*-
import scrapy,os,time
import xlrd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
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
        down_path = os.path.join(settings.DOWNLOAD_DIR, 'atl_tb')
        profile.set_preference('browser.download.dir', down_path)  # 现在文件存放的目录
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, '
                               'text/csv,application/x-msexcel,application/x-excel,application/excel,application/vnd.ms-excel,application/x-download')
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
        time.sleep(3)
        btn_export = driver.find_elements_by_css_selector('.page-nav>button')
        btn_export[5].click()
        time.sleep(100)
        old_list_qty = warehouse_date_data(['ATL', 'ONT', 'KCM'])
        new_qtys = {}
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
                        item['sku'] = table.cell_value(i, 4, )
                        w_name = table.cell_value(i, 0, )
                        if w_name == 'ONT-2':
                            item['warehouse'] = 'ONT'
                        elif w_name == 'KCM-4':
                            item['warehouse'] = 'KCM'
                        else:
                            item['warehouse'] = 'ATL'
                        item['is_new'] = 0
                        qty = table.cell_value(i, 12, )
                        if qty:
                            item['qty'] = qty
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
                os.remove(f_path)

        try:
            driver.refresh()
            driver.switch_to.alert.accept()
            driver.implicitly_wait(100)
        except:
            pass
        display.stop()
        driver.quit()

        update_spiders_logs('ATL', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['ATL', 'ONT', 'KCM'])
