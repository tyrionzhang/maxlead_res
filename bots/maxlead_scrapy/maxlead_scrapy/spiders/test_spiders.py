# -*- coding: utf-8 -*-
import scrapy

class TestSpider(scrapy.Spider):
    name = "test_spider"

    def start_requests(self):
        url = 'http://www.thewarehouseusadata.com/maxlead/inventory.php'
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
            "Connection": "keep-alive",
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin' : 'http://www.thewarehouseusadata.com',
            'Referer' : 'http://www.thewarehouseusadata.com/maxlead/inventory.php'
        }

        # FormRequest 是Scrapy发送POST请求的方法
        yield scrapy.FormRequest(
            url=url,
            headers=headers,
            formdata={"username": "Lead2MAX", "password": "dwf@twu415!", "LC_ACTION": "log in"},
            callback=self.parse_page
        )

    def parse_page(self, response):
        pass
