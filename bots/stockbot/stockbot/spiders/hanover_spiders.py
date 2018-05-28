# -*- coding: utf-8 -*-
import scrapy,os,time
from selenium import webdriver
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds
from django.core.mail import send_mail

class HanoverSpider(scrapy.Spider):
    name = "hanover_spider"
    start_urls = [
        'http://www.telescoassoc.com/prod/hnv/transform.aspx?_h=go&_md=vwInventory&_tpl=vwInventoryList.xsl&_gt=-1&_gs=20&rhash=5adab926c2b523c494&_ha=gmv&spiders=myspiders',
        'https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl={073abe7b-9d71-414d-9933-c71befa9e569}'
    ]
    sku_list = []

    def __init__(self, *args, **kwargs):
        super(HanoverSpider, self).__init__(*args, **kwargs)
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'userSkus_txt.txt')
        with open(file_path, "r") as f:
            sku_list = f.read()
            f.close()
        if sku_list:
            self.sku_list = eval(sku_list)

    def parse(self, response):
        type = response.url[-9:]

        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
        msg_str1 = ''
        msg_str2 = ''
        if type == 'myspiders':
            driver = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)
            driver.get(response.url)
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
            res = driver.find_elements_by_css_selector('#ViewManyListTable tr')
            res.pop(0)
            WarehouseStocks.objects.filter(warehouse='Hanover').delete()
            for val in res:
                item = WarehouseStocksItem()
                td_re = val.find_elements_by_tag_name('td')
                if td_re:
                    item['sku'] = td_re[0].text
                    item['warehouse'] = 'Hanover'
                    if td_re[2].text and not td_re[2].text == ' ':
                        item['qty'] = td_re[2].text
                        item['qty'] = item['qty'].replace(',','')
                    else:
                        item['qty'] = 0
                    yield item

                    threshold = Thresholds.objects.filter(sku=item['sku'], warehouse=item['warehouse'])
                    if threshold and threshold[0].threshold >= int(item['qty']):
                        msg_str2 += 'SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n' % (item['sku'], item['warehouse'], item['qty'], threshold[0].threshold)
            driver.quit()
        else:
            msg_str1 = 'complete\n'
            driver = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)
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
            a_ml = driver.find_elements_by_id('CustomerFacilityGrid_div-cell-0-0')
            if a_ml:
                a_ml[0].click()
                time.sleep(10)
            btn_runreport = driver.find_elements_by_id('btnRunRpt')
            if btn_runreport:
                btn_runreport[0].click()
            iframe1 = driver.find_elements_by_id('ReportFrameStockStatusViewer')
            if iframe1:
                driver.switch_to.frame(iframe1[0])
            iframe2 = driver.find_elements_by_id('report')
            driver.switch_to.frame(iframe2[0])
            time.sleep(30)
            res = driver.find_elements_by_css_selector('.a383 tr')
            res.pop(1)
            res.pop(0)
            res.pop()
            WarehouseStocks.objects.filter(warehouse='EXL').delete()
            for val in res:
                item = WarehouseStocksItem()
                tds = val.find_elements_by_tag_name('td')
                if tds:
                    item['sku'] = tds[0].text
                    item['warehouse'] = 'EXL'
                    if tds[6].text and not tds[6].text == ' ':
                        item['qty'] = tds[6].text
                        item['qty'] = item['qty'].replace(',', '')
                    else:
                        item['qty'] = 0
                    yield item
                    threshold = Thresholds.objects.filter(sku=item['sku'],warehouse=item['warehouse'])
                    if threshold and threshold[0].threshold >= int(item['qty']):
                        msg_str2 += 'SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n' % (item['sku'],item['warehouse'],item['qty'],threshold[0].threshold)
            driver.quit()

        if not os.path.isfile(file_path):
            with open(file_path, "w+") as f:
                f.close()
        with open(file_path, "r+") as f:
            old = f.read()
            f.seek(0)
            if msg_str1:
                f.write(msg_str1)
            f.write(old)
            f.write(msg_str2)
            f.close()

        with open(file_path, "r") as f:
            msg1 = f.readline()
            msg2 = f.readline()
            if msg1 == 'complete\n' and msg2 == 'complete\n':
                send_msg = f.read()
                subject = 'Maxlead库存预警'
                from_email = max_settings.EMAIL_HOST_USER
                send_mail(subject, send_msg, from_email, ['469810717@qq.com'], fail_silently=False)
                f.close()
                os.remove(file_path)


