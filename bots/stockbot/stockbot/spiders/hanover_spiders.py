# -*- coding: utf-8 -*-
import scrapy,os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import spiders_send_email,warehouse_threshold_msgs,warehouse_date_data

class HanoverSpider(scrapy.Spider):
    name = "hanover_spider"

    msg_str1 = "complete\n"
    start_urls = [
        'http://www.telescoassoc.com/prod/hnv/transform.aspx?_h=go&_md=vwInventory&_tpl=vwInventoryList.xsl&_gt=-1&_gs=20&rhash=5adab926c2b523c494&_ha=gmv'
    ]
    sku_list = []
    log_id = None

    def __init__(self, log_id=None, *args, **kwargs):
        super(HanoverSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def parse(self, response):
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH)
        driver.get(response.url)
        driver.implicitly_wait(100)
        elem_code = driver.find_elements_by_id('WarehouseCode')
        elem_acode = driver.find_elements_by_id('AccountCode')
        elem_name = driver.find_elements_by_id('UserName')
        elem_pass = driver.find_elements_by_id('Password')
        btn_login = driver.find_elements_by_css_selector('input[name="Login"]')

        if elem_code:
            elem_code[0].send_keys('03')
        if elem_acode:
            elem_acode[0].send_keys('001862')
        if elem_name:
            elem_name[0].send_keys('MAXLEAD')
        if elem_pass:
            elem_pass[0].send_keys('1202HXML')
        btn_login[0].click()
        driver.implicitly_wait(100)
        total_page = driver.find_elements_by_css_selector('#navigationTR nobr')[0].text
        total_page = int(total_page.split(' ')[-1])

        old_list_qty = warehouse_date_data(['Hanover'])
        new_qtys = {}
        for i in range(total_page):
            try:
                res = driver.find_elements_by_css_selector('#ViewManyListTable tr')
                elem = driver.find_element_by_id('MetaData')
                elem.click()
                res.pop(0)
                for val in res:
                    item = WarehouseStocksItem()
                    td_re = val.find_elements_by_tag_name('td')
                    if td_re:
                        item['sku'] = td_re[0].text
                        item['warehouse'] = 'Hanover'
                        item['is_new'] = 0
                        if td_re[3].text and not td_re[3].text == ' ':
                            item['qty'] = td_re[3].text
                            item['qty'] = item['qty'].replace(',','')
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
                if i < total_page:
                    elem_next_page = driver.find_elements_by_id('Next')
                    if elem_next_page:
                        elem_next_page[0].click()
                        driver.implicitly_wait(100)
            except:
                continue
        display.stop()
        driver.quit()
        update_spiders_logs('Hanover', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['Hanover'])

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
            if msg1 == 'complete\n' and msg2 == 'complete\n' and msg3 == 'complete\n' and msg4 == 'complete\n':
                spiders_send_email(f, file_path=file_path)

