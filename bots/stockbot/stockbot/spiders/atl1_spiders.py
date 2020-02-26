# -*- coding: utf-8 -*-
import scrapy
import json
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.views.views import update_spiders_logs
from maxlead_site.common.common import warehouse_date_data,warehouse_threshold_msgs

class Atl1Spider(scrapy.Spider):
    name = "atl1_spider"
    sku_list = []
    msg_str1 = 'complete\n'
    start_urls = [
        'http://us.hipacking.com/member/passport'
    ]
    log_id = None

    def __init__(self, log_id=None, *args, **kwargs):
        super(Atl1Spider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def start_requests(self):
        url = 'http://us.hipacking.com/member/service/call/getstocks'

        # FormRequest 是Scrapy发送POST请求的方法
        yield scrapy.FormRequest(
            url=url,
            formdata={"uniqueCode": "104136", "password": "1202@hxml"},
            callback=self.parse_page
        )

    def parse_page(self, response):
        res = json.loads(response.text.encode().decode())
        if res['result']:
            new_qtys = {}
            old_list_qty = warehouse_date_data(['ATL', 'ONT', 'KCM'])
            for val in res['data']:
                try:
                    item = WarehouseStocksItem()
                    item['sku'] = val['SellerSKU']
                    w_name = val['WarehouseName']
                    if w_name == 'ONT-2':
                        item['warehouse'] = 'ONT'
                    elif w_name == 'KCM-4':
                        item['warehouse'] = 'KCM'
                    else:
                        item['warehouse'] = 'ATL'
                    item['is_new'] = 0
                    qty = val['Stock']
                    if qty:
                        item['qty'] = qty
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
                except:
                    continue
            update_spiders_logs('ATL', log_id=self.log_id)
            msg_str2 = warehouse_threshold_msgs(new_qtys, ['ATL', 'ONT', 'KCM'])
