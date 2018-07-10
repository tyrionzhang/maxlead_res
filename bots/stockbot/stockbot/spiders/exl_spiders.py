# -*- coding: utf-8 -*-
import scrapy,os,time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from django.core.mail import send_mail

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    msg_str1 = 'complete\n'
    start_urls = ['https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl={073abe7b-9d71-414d-9933-c71befa9e569}']
    sku_list = []

    def __init__(self, username=None, *args, **kwargs):
        super(ExlSpider, self).__init__(*args, **kwargs)
        file_name = 'userSkus_txt.txt'
        if username:
            file_name = 'userSkus_txt_%s.txt' % username
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, file_name)
        with open(file_path, "r") as f:
            sku_list = f.read()
            f.close()
        if sku_list:
            self.sku_list = eval(sku_list)

    def parse(self, response):
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
        msg_str2 = ''
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        chrome_options = Options()
        # chrome_options.add_argument('-headless')
        # chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=settings.CHROME_PATH, service_log_path=settings.LOG_PATH)
        driver.get(response.url)
        elem_name = driver.find_elements_by_id('Loginmodule1_UserName')
        elem_pass = driver.find_elements_by_id('Loginmodule1_Password')
        btn_login = driver.find_elements_by_id('Loginmodule1_Submit1')
        # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')

        if elem_name:
            elem_name[0].send_keys('Maxlead_CS')
        if elem_pass:
            elem_pass[0].send_keys('2015dallas')
        btn_login[0].click()
        a_reports = driver.find_elements_by_id('Menu_Reports_head')
        if a_reports:
            a_reports[0].click()
        a_stock = driver.find_elements_by_css_selector('#Menu_Reports a')
        if a_stock:
            a_stock[0].click()
        rows_res = driver.find_elements_by_id('CustomerFacilityGrid_div-rows')
        list_rows = rows_res[0].find_elements_by_class_name('aw-text-normal')
        if list_rows:
            length = len(list_rows)
            for i in range(0, length):
                if not i == 0:
                    driver.get('https://secure-wms.com/PresentationTier/StockStatusReport.aspx')
                    list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows .aw-text-normal')
                warehouse_name = list_rows[i].find_elements_by_id('CustomerFacilityGrid_div-cell-1-%s' % i)
                if warehouse_name:
                    warehouse_name = warehouse_name[0].text
                list_rows[i].click()
                time.sleep(10)
                btn_runreport = driver.find_elements_by_id('btnRunRpt')
                if btn_runreport:
                    btn_runreport[0].click()
                iframe1 = driver.find_elements_by_id('ReportFrameStockStatusViewer')
                if iframe1:
                    driver.switch_to.frame(iframe1[0])
                iframe2 = driver.find_elements_by_id('report')
                driver.switch_to.frame(iframe2[0])
                res = driver.find_elements_by_css_selector('.a383 tr')
                res.pop(1)
                res.pop(0)
                res.pop()
                for val in res:
                    item = WarehouseStocksItem()
                    tds = val.find_elements_by_tag_name('td')
                    if tds:
                        item['sku'] = tds[0].text
                        if item['sku'] in self.sku_list:
                            item['warehouse'] = warehouse_name
                            if warehouse_name == 'Exchange Logistics':
                                item['warehouse'] = 'EXL'
                            if tds[6].text and not tds[6].text == ' ':
                                item['qty'] = tds[6].text
                                item['qty'] = item['qty'].replace(',', '')
                            else:
                                item['qty'] = 0
                            yield item
                            threshold = Thresholds.objects.filter(sku=item['sku'],warehouse=item['warehouse'])
                            user = SkuUsers.objects.filter(sku=item['sku'])
                            if threshold and threshold[0].threshold >= int(item['qty']):
                                if user:
                                    msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (user[0].user.email,
                                                            item['sku'], item['warehouse'], item['qty'], threshold[0].threshold)
        # display.stop()
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
            if msg1 == 'complete\n' and msg2 == 'complete\n' and msg3 == 'complete\n':
                msg_line = f.read()
                if msg_line:
                    msg_line = msg_line.split('|')
                    msg_line.pop()
                    all_msg = ''
                    subject = 'Maxlead库存预警'
                    from_email = max_settings.EMAIL_HOST_USER

                    msg = {}
                    for i, val in enumerate(msg_line, 1):
                        val = val.split('=>')
                        msg_res_str = val[1]
                        for n, v in enumerate(msg_line, 1):
                            v = v.split('=>')
                            if not n == i and val[0] == v[0]:
                                msg_res_str += v[1]
                        msg.update({val[0]: msg_res_str})
                    for key in msg:
                        all_msg += msg[key]
                        send_mail(subject, msg[key], from_email, [key], fail_silently=False)
                    send_mail(subject, all_msg, from_email, ['shipping.gmi@gmail.com'], fail_silently=False)
                f.close()
                os.remove(file_path)


