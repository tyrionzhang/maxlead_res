# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import csv
import xlrd
from django.db import connection
from django.db.utils import OperationalError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import spiders_send_email,kill_pid_for_name,to_int

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    msg_str1 = 'complete\n'
    start_urls = [
        'https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl={073abe7b-9d71-414d-9933-c71befa9e569}',
        # 'https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl=%7b340efd05-b1c7-453f-be02-39bebb462163%7d&type=myweb'
    ]
    sku_list = []
    stock_names = ['M&L','Match Land','Parts', 'Tradeforce Inc']

    # def __init__(self, username=None, *args, **kwargs):
    #     super(ExlSpider, self).__init__(*args, **kwargs)
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
        type = url[-5:]
        driver.get(url)
        time.sleep(3)
        elem_name = driver.find_elements_by_id('Loginmodule1_UserName')
        elem_pass = driver.find_elements_by_id('Loginmodule1_Password')
        btn_login = driver.find_elements_by_id('Loginmodule1_Submit1')
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
        driver.get('https://secure-wms.com/PresentationTier/StockStatusReport.aspx')
        driver.implicitly_wait(100)
        time.sleep(3)
        list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
        list_rows.pop(0)
        list_rows.pop(-1)
        items = []
        if list_rows:
            length = len(list_rows)
            for i in range(0, length):
                try:
                    if not i == 0:
                        driver.get('https://secure-wms.com/PresentationTier/StockStatusReport.aspx')
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
                    if warehouse_type_name in self.stock_names and warehouse_name:
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
                                if item['sku']:
                                    item['warehouse'] = warehouse_name
                                    if warehouse_name == 'Exchange Logistics':
                                        item['warehouse'] = 'EXL'
                                    if warehouse_name == 'Tradeforce Dayton':
                                        item['warehouse'] = 'TFD'
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
                    continue

        try:
            display.stop()
            driver.quit()
        except IndexError as e:
            print(e)

        querysetlist = []
        date_now = datetime.now()
        for i, val in enumerate(items, 0):
            try:
                for n, v in enumerate(items, 0):
                    if v['sku'] == val['sku'] and not i == n and  val['warehouse'] == v['warehouse']:
                        val['qty'] = int(v['qty']) + int(val['qty'])
                        del items[n]
                date1 = date_now - timedelta(days=1)
                obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse=val['warehouse'],
                                                      created__contains=date1.strftime('%Y-%m-%d'))
                val['qty1'] = 0
                if obj1:
                    val['qty1'] = obj1[0].qty - int(val['qty'])

                querysetlist.append(WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))

                # threshold = Thresholds.objects.filter(sku=val['sku'], warehouse=val['warehouse'])
                # user = SkuUsers.objects.filter(sku=val['sku'])
                # if threshold and threshold[0].threshold >= int(val['qty']):
                #     if user:
                #         msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (
                #             user[0].user.email, val['sku'], val['warehouse'], val['qty'], threshold[0].threshold)
            except OperationalError:
                connection.close()
                connection.cursor()
                continue

        date0 = date_now.strftime('%Y-%m-%d')
        obj = WarehouseStocks.objects.filter(warehouse__in=['EXL', 'TFD', 'ROL'], created__contains=date0)
        try:
            if obj:
                obj.delete()
        except OperationalError:
            connection.close()
            connection.cursor()
            if obj:
                obj.delete()

        WarehouseStocks.objects.bulk_create(querysetlist)
        update_spiders_logs('3pl')
        kill_pid_for_name('postgres')

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
                try:
                    spiders_send_email(f, file_path=file_path)
                except OperationalError:
                    connection.close()
                    connection.cursor()
                    spiders_send_email(f, file_path=file_path)
                lines = os.popen('pgrep firefox')
                for path in lines:
                    try:
                        progress = path.split(' ')[0]
                        if progress:
                            os.popen('kill %s' % progress)
                    except:
                        continue

