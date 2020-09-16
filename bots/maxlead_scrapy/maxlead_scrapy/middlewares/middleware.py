# -*- coding: utf-8 -*-
import random
import requests
import json
import base64
from bots.maxlead_scrapy.maxlead_scrapy.proxy_handle import get_proxy,delete_proxy
from maxlead_site.common.amazon_captcha import CookieList

class ProxyMiddleware(object):
    # def __init__(self, proxy_ip=''):
    #     self.proxy_ip = random.choice(proxy_pool.IPPOOL)


    def process_request(self, request, spider):
        headers = CookieList.get_header()
        # value = '055893146597:666888'
        # value = base64.b64encode(value.encode('utf-8')).decode('utf8')
        # request.meta["proxy"] = 'http://fuyang.placdn.com'
        request.meta.setdefault('dont_filter', True)
        request.headers.setdefault('Referer', 'https://www.amazon.com')
        # request.headers.setdefault('Proxy-Authorization', 'Basic ' + value)
        request.headers.setdefault('Accept', headers['Accept'])
        request.headers.setdefault('Accept-Encoding', headers['Accept-Encoding'])
        request.headers.setdefault('Accept-Language', headers['Accept-Language'])
        request.headers.setdefault('Cache-Control', headers['Cache-Control'])
        request.headers.setdefault('Connection', headers['Connection'])
        request.headers.setdefault('Host', headers['Host'])
        request.headers.setdefault('Upgrade-Insecure-Requests', headers['Upgrade-Insecure-Requests'])
