# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
import MySQLdb
from sshtunnel import SSHTunnelForwarder
from maxlead_res.bots.stocks.stocks import settings

class TwuSpider(scrapy.Spider):
    name = "twu_spider"
    sku_list = []
    msg_str1 = 'complete\n'

    log_id = None

    def __init__(self, *args, **kwargs):
        super(TwuSpider, self).__init__(*args, **kwargs)
        self.server = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),  # B机器的配置
            ssh_password=settings.SSH_PASSWORD,
            ssh_username=settings.SSH_USER,
            remote_bind_address=(settings.MYSQL_HOST, settings.MYSQL_PORT))  # A机器的配置
        self.server.start()
        self.conn = MySQLdb.connect(host='127.0.0.1',  # 此处必须是是127.0.0.1
                                    port=self.server.local_bind_port,
                                    user=settings.MYSQL_USER,
                                    passwd=settings.MYSQL_PASSWORD,
                                    db=settings.MYSQL_DB_NAME)
        self.db_cur = self.conn.cursor()
        check_sql = "select id from mmc_spider_status where warehouse='TWU'"
        status = self.db_cur.execute(check_sql)
        sql = "insert into mmc_spider_status (warehouse, status) values('TWU',1)"
        if status > 0:
            sql = "update mmc_spider_status set status=1 where warehouse='TWU'"
        self.db_cur.execute(sql)
        self.conn.commit()

    def start_requests(self):
        return [Request("http://www.thewarehouseusadata.com/maxlead/inventory.php", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
        try:
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
        finally:
            self.db_cur.close()
            self.conn.close()
            self.server.close()


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

                        values = (warehouse, sku, qty)
                        sql = "insert into mmc_stocks (warehouse, sku, qty) values (%s, %s, %s)"
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
