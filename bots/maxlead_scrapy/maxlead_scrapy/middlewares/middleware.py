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
        url = 'http://api2.uuhttp.com:39002/index/api/return_data?mode=http&count=1&b_time=180&return_type=2&line_break=6&ttl=1&secert=MTg3ODIyOTg2NDk6YTY4ZDdiODNlZWJlYjhkNjFiNWE0Nzg0MDllZWQ4YTA='
        response = requests.get(url)
        if response.status_code == 200:
            res = json.loads(response.text)[0]
            proxy_ip_port = 'http://%s:%s' % (res['ip'], res['port'])
            request.meta["proxy"] = proxy_ip_port
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
        cookie = random.choice(CookieList.get_cookie_from_mongodb())
        request.cookies = cookie
