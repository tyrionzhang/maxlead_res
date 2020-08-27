# -*- coding: utf-8 -*-  
import random
import logging
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from fake_useragent import UserAgent
from bots.maxlead_scrapy.maxlead_scrapy.proxy_handle import get_proxy,delete_proxy


class RandomUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, crawler):
        super(RandomUserAgentMiddleware, self).__init__()
        self.ua = UserAgent()
        # 从settings.py中读取RANDOM_UA_TYPE配置 如果没有则默认值为random  达到可配置的目的
        # 默认是random随机选择，但是可以在配置指定ie或者firefox、chrome等浏览器的不同版本
        self.ua_type = crawler.settings.get("RANDOM_UA_TYPE", "random")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider, dont_filter=True):
        def get_ua():
            """
            函数中的函数 闭包
            读取上面的ua_type设置 让process_request直接调用本get_ua
            """
            return getattr(self.ua, self.ua_type)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Connection": "keep - alive",
            "Access-Control-Allow-Origin": "*"
        }
        ua = get_ua()
        if ua:
            # proxy = "http://" + get_proxy()
            request.meta['download_timeout'] = 30
            # request.meta["proxy"] = proxy
            # print('Url%s Proxy%s ' % (request.url, proxy), end='')

            res_asin = request.url.split('aid=')
            qid = request.url.split('qid=')
            try:
                asin_id = res_asin[1][:10]
                qid = qid[1][:10]
                request.meta.setdefault('aid', asin_id)
                request.meta.setdefault('qid', qid)
                request.meta.setdefault('dont_filter', True)
            except:
                pass
            request.headers.setdefault('User-Agent', ua)
            request.headers.setdefault('Accept', headers['Accept'])
            request.headers.setdefault('Referer', headers['Referer'])
            request.headers.setdefault('Connection', headers['Connection'])
            request.headers.setdefault('Accept-Language', headers['Accept-Language'])
            request.headers.setdefault('Accept-Encoding', headers['Accept-Encoding'])
            request.headers.setdefault('Access-Control-Allow-Origin', headers['Access-Control-Allow-Origin'])

    # def process_exception(self, request, exception, spider):
    #     """
    #     当下载处理器(download handler)或 process_request() (下载中间件)抛出异常
    #     :param response:
    #     :param exception:
    #     :param spider:
    #     :return:
    #         None：继续交给后续中间件处理异常；
    #         Response对象：停止后续process_exception方法
    #         Request对象：停止中间件，request将会被重新调用下载
    #     """
    #     print('Proxy%s，The url%sError:%s' %(request.meta['proxy'],request.url,exception))
    #     import time
    #     time.sleep(5)
    #     if not request.meta['proxy'] == 'http://no proxy!':
    #         delete_proxy(request.meta['proxy'].split("//")[-1])
    #     request.meta['proxy']='http://'+get_proxy()
    #
    #     return request