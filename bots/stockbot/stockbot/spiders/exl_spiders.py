# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from maxlead_site.common.common import spiders_send_email

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    msg_str1 = 'complete\n'
    start_urls = ['https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl={073abe7b-9d71-414d-9933-c71befa9e569}']
    sku_list = []
    stock_names = ['M&L','Match Land','Parts']

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
        chrome_options = Options()
        chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=settings.CHROME_PATH, service_log_path=settings.LOG_PATH)
        driver.get(response.url)
        elem_name = driver.find_elements_by_id('Loginmodule1_UserName')
        elem_pass = driver.find_elements_by_id('Loginmodule1_Password')
        btn_login = driver.find_elements_by_id('Loginmodule1_Submit1')
        # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')

        if elem_name:
            elem_name[0].send_keys('Intybot')
        if elem_pass:
            elem_pass[0].send_keys('7G1#AJjX')
        btn_login[0].click()
        driver.implicitly_wait(100)
        a_reports = driver.find_elements_by_id('Menu_Reports_head')
        if a_reports:
            a_reports[0].click()
        a_stock = driver.find_elements_by_css_selector('#Menu_Reports a')
        if a_stock:
            a_stock[0].click()
        list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
        list_rows.pop(0)
        list_rows.pop(-1)
        if list_rows:
            length = len(list_rows)
            for i in range(0, length):
                if not i == 0:
                    display.stop()
                    from pyvirtualdisplay import Display
                    display = Display(visible=0, size=(800, 800))
                    display.start()
                    chrome_options = Options()
                    chrome_options.add_argument('-headless')
                    chrome_options.add_argument('--disable-gpu')
                    driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=settings.CHROME_PATH,
                                              service_log_path=settings.LOG_PATH)
                    driver.get(response.url)
                    elem_name = driver.find_elements_by_id('Loginmodule1_UserName')
                    elem_pass = driver.find_elements_by_id('Loginmodule1_Password')
                    btn_login = driver.find_elements_by_id('Loginmodule1_Submit1')
                    # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')

                    if elem_name:
                        elem_name[0].send_keys('Intybot')
                    if elem_pass:
                        elem_pass[0].send_keys('7G1#AJjX')
                    btn_login[0].click()
                    driver.implicitly_wait(100)
                    a_reports = driver.find_elements_by_id('Menu_Reports_head')
                    if a_reports:
                        a_reports[0].click()
                    a_stock = driver.find_elements_by_css_selector('#Menu_Reports a')
                    if a_stock:
                        a_stock[0].click()
                    list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
                    list_rows.pop(0)
                    list_rows.pop(-1)
                warehouse_type = list_rows[i].find_elements_by_class_name('aw-column-0')
                warehouse_type_name = warehouse_type[0].text
                if warehouse_type_name in self.stock_names:
                    warehouse_name = list_rows[i].find_elements_by_class_name('aw-column-1')
                    if warehouse_name:
                        warehouse_name = warehouse_name[0].text
                    list_rows[i].click()
                    btn_runreport = driver.find_elements_by_id('btnRunRpt')
                    if btn_runreport:
                        btn_runreport[0].click()
                    iframe1 = driver.find_elements_by_id('ReportFrameStockStatusViewer')
                    driver.implicitly_wait(100)
                    if iframe1:
                        driver.switch_to.frame(iframe1[0])
                    iframe2 = driver.find_elements_by_id('report')
                    driver.implicitly_wait(100)
                    driver.switch_to.frame(iframe2[0])
                    driver.implicitly_wait(100)
                    time.sleep(30)
                    res = driver.find_elements_by_css_selector('.a383 tr')
                    res.pop(1)
                    res.pop(0)
                    res.pop()
                    for val in res:
                        item = WarehouseStocksItem()
                        tds = val.find_elements_by_tag_name('td')
                        if tds:
                            item['sku'] = tds[0].text
                            item['warehouse'] = warehouse_name
                            if warehouse_name == 'Exchange Logistics':
                                item['warehouse'] = 'EXL'
                            if warehouse_name == 'Tradeforce Dayton':
                                item['warehouse'] = 'TFD'
                            if tds[6].text and not tds[6].text == ' ':
                                item['qty'] = tds[6].text
                                item['qty'] = item['qty'].replace(',', '')
                            else:
                                item['qty'] = 0
                            item['is_new'] = 0
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
                            threshold = Thresholds.objects.filter(sku=item['sku'],warehouse=item['warehouse'])
                            user = SkuUsers.objects.filter(sku=item['sku'])
                            if threshold and threshold[0].threshold >= int(item['qty']):
                                if user:
                                    msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (user[0].user.email,
                                                                item['sku'], item['warehouse'], item['qty'], threshold[0].threshold)
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
            if msg1 == 'complete\n' and msg2 == 'complete\n' and msg3 == 'complete\n' and msg4 == 'complete\n':
                spiders_send_email(f, file_path=file_path)


