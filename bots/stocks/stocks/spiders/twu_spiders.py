# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest

class TwuSpider(scrapy.Spider):
    name = "twu_spider"

    def start_requests(self):
        return [Request("http://www.thewarehouseusadata.com/maxlead/inventory.php", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
        try:
            check_sql = "select id from mmc_spider_status where warehouse='TWU'"
            status = self.db_cur.execute(check_sql)
            sql = "insert into mmc_spider_status (warehouse, status) values('TWU',1)"
            if status > 0:
                sql = "update mmc_spider_status set status=1 where warehouse='TWU'"
            self.db_cur.execute(sql)
            self.conn.commit()
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
        except Exception as e:
            sql = "update mmc_spider_status set status=2 where warehouse='TWU'"
            self.db_cur.execute(sql)
            self.conn.commit()

    def parse_page(self, response):
        res = response.css('article')[0].css('table[width="100%"]>tr')
        if res:
            res.pop(1)
            res.pop(0)

            for val in res:
                try:
                    items = val.css('td::text').extract()
                    if items:
                        sku = items[0]
                        warehouse = 'TWU'
                        if items[-1] and not items[-1] == ' ':
                            qty = items[-1]
                            qty = qty.replace(',', '')
                        else:
                            qty = 0

                        qty_sql = "select id from mmc_stocks where commodity_repertory_sku='%s' and warehouse='%s'" % (
                        sku, warehouse)
                        qty_re = self.db_cur.execute(qty_sql)
                        values = (qty, sku, warehouse)
                        if qty_re > 0:
                            sql = "update mmc_stocks set qty=%s where commodity_repertory_sku=%s and warehouse=%s"
                        else:
                            sql = "insert into mmc_stocks (qty, commodity_repertory_sku, warehouse) values (%s, %s, %s)"
                        self.db_cur.execute(sql, values)
                except:
                    continue
            self.conn.commit()
            sql = "update mmc_spider_status set status=3, description='' where warehouse='TWU'"
            self.db_cur.execute(sql)
            self.conn.commit()
        else:
            sql = "update mmc_spider_status set status=2, description=%s where warehouse='TWU'"
            self.db_cur.execute(sql)
            self.conn.commit()
