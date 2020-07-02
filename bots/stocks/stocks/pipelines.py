# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
from sshtunnel import SSHTunnelForwarder
from maxlead_res.bots.stocks.stocks import settings

class StocksPipeline(object):
    # 开启爬虫时执行，只执行一次
    def open_spider(self, spider):
        # spider.hello = "world"  # 为spider对象动态添加属性，可以在spider模块中获取该属性值
        # 可以开启数据库等
        spider.server = SSHTunnelForwarder(
        (settings.SSH_HOST, settings.SSH_PORT),  # B机器的配置
        ssh_password=settings.SSH_PASSWORD,
        ssh_username=settings.SSH_USER,
        remote_bind_address=(settings.MYSQL_HOST, settings.MYSQL_PORT),
        local_bind_address=('127.0.0.1', settings.MYSQL_PORT))  # A机器的配置
        spider.server.start()
        spider.conn = pymysql.connect(host='127.0.0.1',  # 此处必须是是127.0.0.1
                                    port=spider.server.local_bind_port,
                                    user=settings.MYSQL_USER,
                                    password=settings.MYSQL_PASSWORD,
                                    db=settings.MYSQL_DB_NAME,
                                    charset='utf8',
                                    cursorclass=pymysql.cursors.DictCursor)
        spider.db_cur = spider.conn.cursor()

    def process_item(self, item, spider):
        return item

    # 关闭爬虫时执行，只执行一次。 (如果爬虫中间发生异常导致崩溃，close_spider可能也不会执行)
    def close_spider(self, spider):
        # 可以关闭数据库等
        spider.db_cur.close()
        spider.conn.close()
        spider.server.close()
