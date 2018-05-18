# -*- coding: utf-8 -*-
import scrapy,requests,time
from scrapy.http import Request, FormRequest
from selenium import webdriver
from bots.maxlead_scrapy.maxlead_scrapy import settings
from maxlead_site.common.excel_world import get_excel_file1

class TestSpider(scrapy.Spider):
    name = "test_spider"

    start_urls = ['http://www.telescoassoc.com/prod/hnv/transform.aspx?_h=go&_md=vwInventory&_tpl=vwInventoryList.xsl&_gt=-1&_gs=20&rhash=5adab926c2b523c494&_ha=gmv']

    def parse(self, response):
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
        fields = []
        data = []
        re = {}
        res = driver.find_elements_by_css_selector('#ViewManyListTable tr')
        for v in res[0].find_elements_by_tag_name('td'):
            fields.append(v.text)
        res.pop(0)
        for val in res:
            td_re = val.find_elements_by_tag_name('td')
            for i,v in enumerate(td_re,0):
                re.update({fields[i]:v.text})
            data.append(re)
            re = {}
        get_excel_file1(self, data, fields, fields, 'Hanover')

    # start_urls = ['https://secure-wms.com/PresentationTier/LoginForm.aspx?3pl={073abe7b-9d71-414d-9933-c71befa9e569}']
    #
    # def parse(self, response):
    #     driver = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)
    #     driver.get(response.url)
    #     elem_name = driver.find_elements_by_id('Loginmodule1_UserName')
    #     elem_pass = driver.find_elements_by_id('Loginmodule1_Password')
    #     btn_login = driver.find_elements_by_id('Loginmodule1_Submit1')
    #     # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')
    #
    #     if elem_name:
    #         elem_name[0].send_keys('Maxlead_CS')
    #     if elem_pass:
    #         elem_pass[0].send_keys('2015dallas')
    #     btn_login[0].click()
    #     a_reports = driver.find_elements_by_id('Menu_Reports_head')
    #     if a_reports:
    #         a_reports[0].click()
    #     a_stock = driver.find_elements_by_css_selector('#Menu_Reports a')
    #     if a_stock:
    #         a_stock[0].click()
    #     a_ml = driver.find_elements_by_id('CustomerFacilityGrid_div-cell-0-0')
    #     if a_ml:
    #         a_ml[0].click()
    #         time.sleep(10)
    #     btn_runreport = driver.find_elements_by_id('btnRunRpt')
    #     if btn_runreport:
    #         btn_runreport[0].click()
    #     iframe1 = driver.find_elements_by_id('ReportFrameStockStatusViewer')
    #     if iframe1:
    #         driver.switch_to.frame(iframe1[0])
    #     iframe2 = driver.find_elements_by_id('report')
    #     driver.switch_to.frame(iframe2[0])
    #     res = driver.find_elements_by_css_selector('.a383 tr')
    #     fields = []
    #     data = []
    #     re = {}
    #     for v in res[1].find_elements_by_tag_name('td'):
    #         fields.append(v.text)
    #     res.pop(1)
    #     res.pop(0)
    #     res.pop()
    #     for val in res:
    #         tds = val.find_elements_by_tag_name('td')
    #         for i,v in enumerate(tds,0):
    #             re.update({fields[i]:v.text})
    #         data.append(re)
    #         re = {}
    #     get_excel_file1(self, data, fields, fields,'EXL')


    # def start_requests(self):
    #     return [Request("http://www.thewarehouseusadata.com/maxlead/inventory.php", meta={'cookiejar': 1}, callback=self.post_login)]
    #
    # def post_login(self, response):
    #     headers = {
    #         "Accept": "*/*",
    #         "Accept-Encoding": "gzip,deflate",
    #         "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
    #         "Connection": "keep-alive",
    #         'Content-Type': 'application/x-www-form-urlencoded',
    #         'Origin' : 'http://www.thewarehouseusadata.com',
    #         'Referer' : 'http://www.thewarehouseusadata.com/maxlead/inventory.php'
    #     }
    #
    #     return [FormRequest.from_response(response,
    #                                       meta={'cookiejar': response.meta['cookiejar']},
    #                                       headers=headers,  # 注意此处的headers
    #                                       formdata={
    #                                           'username': 'Lead2MAX',
    #                                           'password': 'dwf@twu415!'
    #                                       },
    #                                       callback=self.parse_page,
    #                                       dont_filter=True
    #                                       )]
    #
    #
    # def parse_page(self, response):
    #     res = response.css('article')[0].css('table[width="100%"]>tr')
    #     data = []
    #     if res:
    #         fields = res[1].css('td::text').extract()
    #         res.pop(1)
    #         res.pop(0)
    #         fields.pop(0)
    #         fields[6] = 'reservedopen'
    #         for val in res:
    #             items = val.css('td::text').extract()
    #             re = {
    #                 'SKU':items[0],
    #                 'description':items[1],
    #                 'received qty':items[2].split('=')[1],
    #                 'return qty':items[3].split('=')[1],
    #                 'total received':items[4].split('=')[1],
    #                 'reserved today':items[5].split('=')[1],
    #                 'reservedopen':items[6].split('=')[1],
    #                 'reserved onhold':items[7].split('=')[1],
    #                 'tracked':items[8].split('=')[1],
    #                 'total':items[9].split('=')[1],
    #                 'qty remaining':items[10],
    #                 'less reserved':items[11],
    #             }
    #             data.append(re)
    #         get_excel_file1(self, data, fields, fields)

