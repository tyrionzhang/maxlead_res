# -*- coding: utf-8 -*-
import scrapy,requests,time
from scrapy.http import Request, FormRequest
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks

class TwuSpider(scrapy.Spider):
    name = "twu_spider"

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
                                              'username': 'Lead2MAX',
                                              'password': 'dwf@twu415!'
                                          },
                                          callback=self.parse_page,
                                          dont_filter=True
                                          )]


    def parse_page(self, response):
        res = response.css('article')[0].css('table[width="100%"]>tr')
        if res:
            fields = res[1].css('td::text').extract()
            res.pop(1)
            res.pop(0)
            fields.pop(0)
            WarehouseStocks.objects.filter(warehouse='TWU').delete()
            for val in res:
                item = WarehouseStocksItem()
                items = val.css('td::text').extract()
                if items:
                    item['sku'] = items[0]
                    item['warehouse'] = 'TWU'
                    if items[11]:
                        item['qty'] = items[11]
                    yield item
