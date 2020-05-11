# -*- coding: utf-8 -*-
import scrapy
import json
import MySQLdb
from sshtunnel import SSHTunnelForwarder
from maxlead_res.bots.stocks.stocks import settings

class Atl1Spider(scrapy.Spider):
    name = "atl1_spider"
    log_id = None

    def __init__(self, *args, **kwargs):
        super(Atl1Spider, self).__init__(*args, **kwargs)
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
        check_sql = "select id from mmc_spider_status where warehouse='ATL1'"
        status = self.db_cur.execute(check_sql)
        sql = "insert into mmc_spider_status (warehouse, status) values('ATL1',1)"
        if status > 0:
            sql = "update mmc_spider_status set status=1 where warehouse='ATL1'"
        self.db_cur.execute(sql)
        self.conn.commit()

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
        self.db_cur.close()
        self.conn.close()
        self.server.close()