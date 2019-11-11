# -*- coding: utf-8 -*-
import scrapy,os
from scrapy.http import Request, FormRequest
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.views.views import update_spiders_logs
from maxlead import settings as max_settings
from maxlead_site.common.common import spiders_send_email,warehouse_threshold_msgs,warehouse_date_data

class TwuSpider(scrapy.Spider):
    name = "twu_spider"
    sku_list = []
    msg_str1 = 'complete\n'

    log_id = None

    def __init__(self, log_id=None, *args, **kwargs):
        super(TwuSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def start_requests(self):
        return [Request("http://www.thewarehouseusadata.com/maxlead/inventory.php", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
            "Connection": "keep-alive",
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin' : 'http://www.thewarehouseusadata.com',
            'Referer' : 'http://www.thewarehouseusadata.com/maxlead/inventory.php'
        }

        return [FormRequest.from_response(response,
                                          meta={'cookiejar': response.meta['cookiejar']},
                                          headers=headers,  # 注意此处的headers
                                          formdata={
                                              'username': 'maxlead',
                                              'password': 'legwork/M103'
                                          },
                                          callback=self.parse_page,
                                          dont_filter=True
                                          )]


    def parse_page(self, response):
        res = response.css('article')[0].css('table[width="100%"]>tr')
        new_qtys = {}
        if res:
            fields = res[1].css('td::text').extract()
            res.pop(1)
            res.pop(0)
            fields.pop(0)

            old_list_qty = warehouse_date_data(['TWU'])
            for val in res:
                item = WarehouseStocksItem()
                items = val.css('td::text').extract()
                if items:
                    item['sku'] = items[0]
                    item['warehouse'] = 'TWU'
                    item['is_new'] = 0
                    if items[11] and not items[11] == ' ':
                        item['qty'] = items[11]
                        item['qty'] = item['qty'].replace(',', '')
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
        update_spiders_logs('TWU', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['TWU'])
