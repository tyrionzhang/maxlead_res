# -*- coding: utf-8 -*-

import scrapy,time,os,re
import urllib
from bots.maxlead_scrapy.maxlead_scrapy.items import CategoryRankItem
from maxlead_site.models import UserAsins,Listings
from django.db.models import Count
from selenium import webdriver
from bots.maxlead_scrapy.maxlead_scrapy import settings


class CatrankSpider(scrapy.Spider):
    name = "catrank_spider"
    start_urls = []
    url = "https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias=aps&field-keywords=%s&asin=%s"
    url1 = 'https://www.amazon.com/gp/search/ref=sr_hi_1?fst=p90x:1&rh=n:%s,k:%s&keywords=%s&ie=UTF8&qid=%s&asin=%s'
    res = list(UserAsins.objects.filter(is_use=True).values('aid'))
    check = False

    if res:
        for re in res:
            asins = UserAsins.objects.values('id', 'aid', 'cat1', 'cat2', 'cat3', 'keywords1', 'keywords2', 'keywords3').\
                                                filter(aid=re['aid'])[0]
            if asins['keywords1']:
                keywords1 = asins['keywords1'].split(',')
                for val in keywords1:
                    url_k = url % (val, asins['aid'])
                    start_urls.append(url_k)
                    if asins['cat1']:
                        url_c = url1 % (asins['cat1'], val, val, int(time.time()), asins['aid'])
                        start_urls.append(url_c)
            if asins['keywords2']:
                keywords2 = asins['keywords2'].split(',')
                for val in keywords2:
                    url_k = url % (val, asins['aid'])
                    start_urls.append(url_k)
                    if asins['cat2']:
                        url_c = url1 % (asins['cat2'], val, val, int(time.time()), asins['aid'])
                        start_urls.append(url_c)
            if asins['keywords3']:
                keywords3 = asins['keywords3'].split(',')
                for val in keywords3:
                    url_k = url % (val, asins['aid'])
                    start_urls.append(url_k)
                    if asins['cat3']:
                        url_c = url1 % (asins['cat3'], val, val, int(time.time()), asins['aid'])
                        start_urls.append(url_c)

    def parse(self, response):
        url = urllib.parse.unquote(response.url)
        res_asin = url.split('asin=')
        field_keywords = url.split('field-keywords=')
        keywords = url.split('k:')
        cats = url.split('rh=n:')
        self.check = False
        for val in response.css('li.celwidget'):
            item = CategoryRankItem()
            item['user_asin'] = res_asin[1]
            item['asin'] = val.css('li.celwidget::attr(data-asin)').extract_first()
            if item['asin']:
                if item['user_asin'] == item['asin']:
                    self.check = True
                rank = val.css('li.celwidget::attr(id)').extract_first()
                if rank:
                    item['rank'] = int(rank.split('_')[1])+1
                if len(field_keywords) == 2:
                    item['keywords'] = field_keywords[1].split('&')[0]
                if len(keywords) == 2:
                    item['keywords'] = keywords[1].split('&')[0]
                if len(cats) == 2:
                    item['cat'] = cats[1].split(',k:')[0]
                ad = val.css('h5::text').extract_first()
                if ad:
                    item['is_ad'] = 1
                if self.check:
                    yield item
                    break
                else:
                    yield item

        if not self.check:
            next_page = response.css('a#pagnNextLink ::attr("href")').extract_first()
            if next_page is not None:
                page = next_page.split('page=')
                page = page[1].split('&')[0]
                if int(page)<=20:
                    next_page = response.urljoin(next_page)
                    next_page = next_page + '&asin='+res_asin[1]
                    yield scrapy.Request(next_page, callback=self.parse)