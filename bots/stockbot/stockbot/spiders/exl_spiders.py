# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import xlrd
import requests
import json
from django.db import connection
from django.db.utils import OperationalError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from max_stock.views.views import update_spiders_logs,check_spiders,get_3pl_token
from maxlead_site.common.common import spiders_send_email,kill_pid_for_name,to_int,warehouse_threshold_msgs,warehouse_date_data

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    msg_str1 = 'complete\n'
    start_urls = [
        'https://secure-wms.com/smartui/?tplguid={073abe7b-9d71-414d-9933-c71befa9e569}'
    ]
    sku_list = []
    log_id = None
    stock_names = ['M&L','Match Land','Parts']

    def __init__(self, log_id=None, *args, **kwargs):
        super(ExlSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def parse(self, response):
        items = []
        token_str = get_3pl_token()
        if token_str:
            url1 = 'https://secure-wms.com/inventory/stocksummaries?pgsiz=500&pgnum=1&rql=facilityId=in=(1, 2, 3)'
            headers = {
                'Content-Type': "application/json; charset=utf-8",
                'Accept': "application/hal+json",
                'Host': "secure-wms.com",
                'Accept-Language': "en-US,en;q=0.8",
                'Accept-Encoding': "gzip,deflate,sdch",
                'Authorization': 'Bearer %s' % token_str
            }
            # ware = requests.get('https://secure-wms.com/properties/facilities/summaries?customerId=3', headers=headers)
            while 1:
                res_3pl = requests.get(url1, headers=headers)
                if res_3pl.status_code == 200:
                    res = json.loads(res_3pl.content.decode())
                    for val in res['summaries']:
                        item = {}
                        item['sku'] = val['itemIdentifier']['sku']
                        if val['facilityId'] == 1:
                            item['warehouse'] = 'EXL'
                        elif val['facilityId'] == 3:
                            item['warehouse'] = 'TFD'
                        else:
                            item['warehouse'] = 'ROL'
                        item['qty'] = to_int(val['available'])
                        items.append(item)
                    if 'next' not in res['_links']:
                        break
                    url1 = 'https://secure-wms.com%s' % res['_links']['next']['href']

        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.dir', settings.DOWNLOAD_DIR)  # 现在文件存放的目录
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, '
                                             'text/csv,application/x-msexcel,application/x-excel,application/excel,application/vnd.ms-excel')
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)
        url = response.url
        driver.get(url)
        time.sleep(3)
        elem_name = driver.find_elements_by_id('login')
        elem_pass = driver.find_elements_by_id('password')
        btn_login = driver.find_elements_by_css_selector('input[type="submit"]')
        # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')

        # if type == 'myweb':
        #     if elem_name:
        #         elem_name[0].send_keys('Dteng')
        #     if elem_pass:
        #         elem_pass[0].send_keys('Tr@d3')
        # else:
        if elem_name:
            elem_name[0].send_keys('Intybot')
        if elem_pass:
            elem_pass[0].send_keys('7G1#AJjX')
        btn_login[0].click()
        driver.implicitly_wait(100)
        driver.get('https://secure-wms.com/WebUI/V1/V1Link/StockStatusReport.aspx')
        driver.implicitly_wait(100)
        time.sleep(3)
        close_guide = driver.find_elements_by_css_selector('#pendo-guide-container>button')
        if close_guide:
            print('---------------Click f65b1092!!!!')
            close_guide[0].click()
        list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
        list_rows.pop(0)
        list_rows.pop(-1)
        if list_rows:
            length = len(list_rows)
            for i in range(0, length):
                try:
                    if not i == 0:
                        driver.get('https://secure-wms.com/WebUI/V1/V1Link/StockStatusReport.aspx')
                        driver.implicitly_wait(100)
                        time.sleep(3)
                        list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
                        list_rows.pop(0)
                        list_rows.pop(-1)
                    warehouse_type = list_rows[i].find_elements_by_class_name('aw-column-0')
                    warehouse_name = list_rows[i].find_elements_by_class_name('aw-column-1')
                    warehouse_type_name = warehouse_type[0].text
                    if warehouse_name:
                        warehouse_name = warehouse_name[0].text
                    if warehouse_type_name in self.stock_names and warehouse_name and warehouse_name == 'ROL':
                        list_rows[i].find_element_by_tag_name('span').click()
                        btn_runreport = driver.find_elements_by_id('btnRunRpt')
                        if btn_runreport:
                            btn_runreport[0].click()
                            driver.implicitly_wait(100)
                        while 1:
                            table_re = driver.find_elements_by_id("StockStatusViewer")
                            if not table_re:
                                driver.refresh()
                                driver.switch_to.alert.accept()
                                driver.implicitly_wait(100)
                                time.sleep(20)
                            try:
                                Select(driver.find_element_by_id("StockStatusViewer__ctl1__ctl5__ctl0")).select_by_value('EXCELOPENXML')
                                driver.find_element_by_id("StockStatusViewer__ctl1__ctl5__ctl1").click()
                                break
                            except:
                                print('Error Element!')

                        time.sleep(120)
                        files = '%sStockwithLocation.xlsx' % settings.DOWNLOAD_DIR
                        data = xlrd.open_workbook(files)  # 打开fname文件
                        data.sheet_names()  # 获取xls文件中所有sheet的名称
                        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
                        nrows = table.nrows
                        for i in range(nrows):
                            try:
                                i = i+7
                                if i >= nrows:
                                    break
                                item = {}
                                item['sku'] = table.cell_value(i, 0,)
                                if len(item['sku']) > 225:
                                    continue
                                if item['sku']:
                                    item['warehouse'] = warehouse_name
                                    # if warehouse_name == 'Exchange Logistics':
                                    #     item['warehouse'] = 'EXL'
                                    # if warehouse_name == 'Tradeforce Dayton':
                                    #     item['warehouse'] = 'TFD'
                                    if warehouse_name == 'ROL':
                                        item['warehouse'] = 'ROL'
                                    if table.cell_value(i, 11,) and not table.cell_value(i, 11,) == ' ':
                                        item['qty'] = table.cell_value(i, 11,)
                                        item['qty'] = to_int(item['qty'])
                                    else:
                                        item['qty'] = 0
                                    items.append(item)
                            except:
                                continue
                        os.remove(files)
                        # f = open(files, 'r', encoding='UTF-8')
                        # csv_files = csv.reader(f)
                        # for i, val in enumerate(csv_files, 0):
                        #     try:
                        #         if i > 0:
                        #             item = WarehouseStocksItem()
                        #             item['sku'] = val[0]
                        #             item['warehouse'] = val[2]
                        #             if warehouse_name == 'Exchange Logistics':
                        #                 item['warehouse'] = 'EXL'
                        #             if warehouse_name == 'Tradeforce Dayton':
                        #                 item['warehouse'] = 'TFD'
                        #             if warehouse_name == 'Roll On Logistics':
                        #                 item['warehouse'] = 'ROL'
                        #             if val[20] and not val[20] == ' ':
                        #                 item['qty'] = val[20]
                        #                 item['qty'] = to_int(item['qty'].replace(',', ''))
                        #             else:
                        #                 item['qty'] = 0
                        #             items.append(item)
                        #     except:
                        #         continue
                        # f.close()
                except:
                    close_guide = driver.find_elements_by_css_selector('#pendo-guide-container>button')
                    if close_guide:
                        print('---------------Click f65b1092!!!!')
                        close_guide[0].click()
                    continue

        try:
            display.stop()
            driver.quit()
        except IndexError as e:
            print(e)

        querysetlist = []
        old_list_qty = warehouse_date_data(['EXL', 'TFD', 'ROL'])
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
                connection.close()
                continue

        WarehouseStocks.objects.bulk_create(querysetlist)
        new_log = update_spiders_logs('3pl', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['EXL', 'TFD', 'ROL'])
        check_spiders(new_log)
        try:
            spiders_send_email()
        except OperationalError:
            connection.close()
            connection.cursor()
            spiders_send_email()

