# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json
from django.db import connection
from django.db.utils import OperationalError
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from max_stock.views.views import update_spiders_logs,check_spiders,get_3pl_token
from maxlead_site.common.common import spiders_send_email,kill_pid_for_name,to_int,warehouse_threshold_msgs,warehouse_date_data

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    items = []
    log_id = None
    new_qtys = {}
    headers = ''

    def __init__(self, log_id=None, *args, **kwargs):
        super(ExlSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)
        token_str = get_3pl_token()
        self.headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept': "application/hal+json",
            'Host': "secure-wms.com",
            'Accept-Language': "en-US,en;q=0.8",
            'Accept-Encoding': "gzip,deflate,sdch",
            'Authorization': 'Bearer %s' % token_str
        }

    def start_requests(self):
        url1 = 'https://secure-wms.com/inventory/stocksummaries?pgsiz=500&pgnum=1&rql=facilityId=in=(1, 2, 3)'
        yield Request(url1, headers=self.headers)

    def parse(self, response):
        res = json.loads(response.text.encode().decode())
        for val in res['summaries']:
            try:
                item = {}
                item['sku'] = val['itemIdentifier']['sku']
                if val['facilityId'] == 1:
                    item['warehouse'] = 'EXL'
                elif val['facilityId'] == 3:
                    item['warehouse'] = 'TFD'
                else:
                    item['warehouse'] = 'ROL'
                item['qty'] = to_int(val['available'])
                self.items.append(item)
            except:
                continue
        if 'next' in res['_links']:
            next_page = 'https://secure-wms.com%s' % res['_links']['next']['href']
            yield scrapy.Request(next_page, callback=self.parse, headers=self.headers, dont_filter=True)
        else:
            querysetlist = []
            old_list_qty = warehouse_date_data(['EXL', 'TFD', 'ROL'])
            for i, val in enumerate(self.items, 0):
                if len(val['sku']) > 50:
                    continue
                try:
                    for n, v in enumerate(self.items, 0):
                        if v['sku'] == val['sku'] and not i == n and val['warehouse'] == v['warehouse']:
                            val['qty'] = int(v['qty']) + int(val['qty'])
                            del self.items[n]
                    val['qty1'] = 0
                    if old_list_qty:
                        key1 = val['warehouse'] + val['sku']
                        if key1 in old_list_qty:
                            val['qty1'] = old_list_qty[key1] - int(val['qty'])

                    querysetlist.append(
                        WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))
                    new_key = val['warehouse'] + val['sku']
                    self.new_qtys.update({
                        new_key: val['qty']
                    })
                except OperationalError:
                    connection.cursor()
                    for n, v in enumerate(self.items, 0):
                        if v['sku'] == val['sku'] and not i == n and val['warehouse'] == v['warehouse']:
                            val['qty'] = int(v['qty']) + int(val['qty'])
                            del self.items[n]
                    val['qty1'] = 0
                    if old_list_qty:
                        key1 = val['warehouse'] + val['sku']
                        if key1 in old_list_qty:
                            val['qty1'] = old_list_qty[key1] - int(val['qty'])

                    querysetlist.append(
                        WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))

                    new_key = val['warehouse'] + val['sku']
                    self.new_qtys.update({
                        new_key: val['qty']
                    })
                    connection.close()
                    continue

            WarehouseStocks.objects.bulk_create(querysetlist)

            new_log = update_spiders_logs('3pl', log_id=self.log_id)
            msg_str2 = warehouse_threshold_msgs(self.new_qtys, ['EXL', 'TFD', 'ROL'])
            check_spiders(new_log)
            try:
                spiders_send_email()
            except OperationalError:
                connection.cursor()
                spiders_send_email()
                connection.close()

