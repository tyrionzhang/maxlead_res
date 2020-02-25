# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import xlrd
import requests
import json
from django.db import connection
from django.db.utils import OperationalError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from bots.stockbot.stockbot import settings
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from max_stock.views.views import update_spiders_logs,check_spiders,get_3pl_token
from maxlead_site.common.common import spiders_send_email,kill_pid_for_name,to_int,warehouse_threshold_msgs,warehouse_date_data

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    msg_str1 = 'complete\n'
    start_urls = [
        'https://secure-wms.com/smartui/?tplguid={073abe7b-9d71-414d-9933-c71befa9e569}'
    ]
    sku_list = []
    log_id = None
    stock_names = ['M&L','Match Land','Parts']

    def __init__(self, log_id=None, *args, **kwargs):
        super(ExlSpider, self).__init__(*args, **kwargs)
        if log_id:
            self.log_id = int(log_id)

    def parse(self, response):
        items = []
        token_str = get_3pl_token()
        if token_str:
            url1 = 'https://secure-wms.com/inventory/stocksummaries?pgsiz=500&pgnum=1&rql=facilityId=in=(1, 2, 3)'
            headers = {
                'Content-Type': "application/json; charset=utf-8",
                'Accept': "application/hal+json",
                'Host': "secure-wms.com",
                'Accept-Language': "en-US,en;q=0.8",
                'Accept-Encoding': "gzip,deflate,sdch",
                'Authorization': 'Bearer %s' % token_str
            }
            # ware = requests.get('https://secure-wms.com/properties/facilities/summaries?customerId=3', headers=headers)
            while 1:
                res_3pl = requests.get(url1, headers=headers)
                if res_3pl.status_code == 200:
                    res = json.loads(res_3pl.content.decode())
                    for val in res['summaries']:
                        item = {}
                        item['sku'] = val['itemIdentifier']['sku']
                        if val['facilityId'] == 1:
                            item['warehouse'] = 'EXL'
                        elif val['facilityId'] == 3:
                            item['warehouse'] = 'TFD'
                        else:
                            item['warehouse'] = 'ROL'
                        item['qty'] = to_int(val['available'])
                        items.append(item)
                    if 'next' not in res['_links']:
                        break
                    url1 = 'https://secure-wms.com%s' % res['_links']['next']['href']
        querysetlist = []
        old_list_qty = warehouse_date_data(['EXL', 'TFD', 'ROL'])
        new_qtys = {}
        for i, val in enumerate(items, 0):
            if len(val['sku']) > 50:
                continue
            try:
                for n, v in enumerate(items, 0):
                    if v['sku'] == val['sku'] and not i == n and  val['warehouse'] == v['warehouse']:
                        val['qty'] = int(v['qty']) + int(val['qty'])
                        del items[n]
                val['qty1'] = 0
                if old_list_qty:
                    key1 = val['warehouse'] + val['sku']
                    if key1 in old_list_qty:
                        val['qty1'] = old_list_qty[key1] - int(val['qty'])

                querysetlist.append(WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))
                new_key = val['warehouse'] + val['sku']
                new_qtys.update({
                    new_key: val['qty']
                })
            except OperationalError:
                connection.cursor()
                for n, v in enumerate(items, 0):
                    if v['sku'] == val['sku'] and not i == n and  val['warehouse'] == v['warehouse']:
                        val['qty'] = int(v['qty']) + int(val['qty'])
                        del items[n]
                val['qty1'] = 0
                if old_list_qty:
                    key1 = val['warehouse'] + val['sku']
                    if key1 in old_list_qty:
                        val['qty1'] = old_list_qty[key1] - int(val['qty'])

                querysetlist.append(WarehouseStocks(sku=val['sku'], warehouse=val['warehouse'], qty=val['qty'], qty1=val['qty1']))

                new_key = val['warehouse'] + val['sku']
                new_qtys.update({
                    new_key: val['qty']
                })
                connection.close()
                continue

        WarehouseStocks.objects.bulk_create(querysetlist)
        new_log = update_spiders_logs('3pl', log_id=self.log_id)
        msg_str2 = warehouse_threshold_msgs(new_qtys, ['EXL', 'TFD', 'ROL'])
        check_spiders(new_log)
        try:
            spiders_send_email()
        except OperationalError:
            connection.cursor()
            spiders_send_email()
            connection.close()

