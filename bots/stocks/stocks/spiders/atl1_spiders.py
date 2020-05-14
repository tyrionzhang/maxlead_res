# -*- coding: utf-8 -*-
import scrapy
import json

class Atl1Spider(scrapy.Spider):
    name = "atl1_spider"

    def start_requests(self):
        try:
            check_sql = "select id from mmc_spider_status where warehouse='ATL1'"
            status = self.db_cur.execute(check_sql)
            sql = "insert into mmc_spider_status (warehouse, status) values('ATL1',1)"
            if status > 0:
                sql = "update mmc_spider_status set status=1 where warehouse='ATL1'"
            self.db_cur.execute(sql)
            self.conn.commit()

            url = 'http://us.hipacking.com/member/service/call/getstocks'

            # FormRequest 是Scrapy发送POST请求的方法
            yield scrapy.FormRequest(
                url=url,
                formdata={"uniqueCode": "104136", "password": "1202@hxml"},
                callback=self.parse_page
            )
        except Exception as e:
            sql = "update mmc_spider_status set status=2 where warehouse='ATL1'"
            self.db_cur.execute(sql)
            self.conn.commit()

    def parse_page(self, response):
        res = json.loads(response.text.encode().decode())
        if res['result']:
            for val in res['data']:
                try:
                    sku = val['SellerSKU']
                    w_name = val['WarehouseName']
                    if w_name == 'ONT-2':
                        warehouse = 'ONT'
                    elif w_name == 'KCM-4':
                        warehouse = 'KCM'
                    elif w_name == 'ATL-3':
                        warehouse = 'ATL-3'
                    else:
                        warehouse = 'ATL'
                    qty = val['Stock']
                    if not qty:
                        qty = 0
                    values = (warehouse, sku, qty)
                    sql = "insert into mmc_stocks (warehouse, sku, qty) values (%s, %s, %s)"
                    self.db_cur.execute(sql, values)
                except:
                    continue
            self.conn.commit()
            sql = "update mmc_spider_status set status=3, description='' where warehouse='ATL1'"
            self.db_cur.execute(sql)
            self.conn.commit()
        else:
            sql = "update mmc_spider_status set status=2 where warehouse='ATL1'"
            self.db_cur.execute(sql)
            self.conn.commit()
