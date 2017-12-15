# -*- coding: utf-8 -*-

import scrapy,time,os
from maxlead_site.models import UserAsins
from django.db.models import Count

class QaSpider(scrapy.Spider):

    name = "qa_spider"
    start_urls = []
    url = "https://www.amazon.com/ask/questions/asin/%s/"
    res = list(UserAsins.objects.filter(is_use=True).values('aid','review_watcher','listing_watcher','sku').annotate(count=Count('aid')))

    if res:
        for re in res:
            asin = url % (re['aid'])
            start_urls.append(asin)

    def parse(self, response):
        next_page = response.css('div#askPaginationBar li.a-last a::attr("href")').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)