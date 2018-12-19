# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bots.maxlead_scrapy.maxlead_scrapy.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from bots.maxlead_scrapy.maxlead_scrapy import settings
from maxlead import settings as max_settings
from maxlead_site.common.common import spiders_send_email

class TwuSpider(scrapy.Spider):
    name = "twu_spider"
    sku_list = []
    start_urls = ["http://www.thewarehouseusadata.com/maxlead/inventory.php"]
    msg_str1 = 'complete\n'

    # def __init__(self, username=None, *args, **kwargs):
    #     super(TwuSpider, self).__init__(*args, **kwargs)
    #     file_name = 'userSkus_txt.txt'
    #     if username:
    #         file_name = 'userSkus_txt_%s.txt' % username
    #     file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, file_name)
    #     with open(file_path, "r") as f:
    #         sku_list = f.read()
    #         f.close()
    #     if sku_list:
    #         self.sku_list = eval(sku_list)

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


    def parse(self, response):
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        chrome_options = Options()
        # chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=settings.CHROME_PATH,
                                  service_log_path=settings.LOG_PATH)
        driver.get(response.url)
        elem_name = driver.find_elements_by_name('username')
        elem_pass = driver.find_elements_by_name('password')
        btn_login = driver.find_elements_by_name('LC_ACTION')

        if elem_name:
            elem_name[0].send_keys('Lead2MAX')
        if elem_pass:
            elem_pass[0].send_keys('dwf@twu415!')
        btn_login[0].click()
        driver.implicitly_wait(100)
        res = driver.find_elements_by_css_selector('article table[width="100%"]>tbody>tr')
        if res:
            res.pop(1)
            res.pop(0)
            msg_str2 = ''
            file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
            for val in res:
                item = WarehouseStocksItem()
                items = val.find_elements_by_tag_name('td')
                if items:
                    item['sku'] = items[1].text
                    item['warehouse'] = 'TWU'
                    item['is_new'] = 0
                    qty = items[13].text
                    if qty and not qty == ' ':
                        item['qty'] = qty
                        item['qty'] = item['qty'].replace(',', '')
                    else:
                        item['qty'] = 0
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
                    threshold = Thresholds.objects.filter(sku=item['sku'], warehouse=item['warehouse'])
                    user = SkuUsers.objects.filter(sku=item['sku'])
                    if threshold and threshold[0].threshold >= int(item['qty']):
                        if user:
                            msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (user[0].user.email,
                                                item['sku'], item['warehouse'],item['qty'], threshold[0].threshold)

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
        # display.stop()
        driver.quit()