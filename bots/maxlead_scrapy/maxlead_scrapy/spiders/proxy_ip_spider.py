# -*- coding: utf-8 -*-

import scrapy,requests,time
from bots.maxlead_scrapy.maxlead_scrapy.items import ProxyIpItem
from maxlead_site.models import ProxyIp


class ProxyIpSpider(scrapy.Spider):

    name = "proxy_ip_spider"
    start_urls = ['https://www.xicidaili.com/nn/']

    def parse(self, response):
        time.sleep(3)
        all_trs = response.css('#ip_list tr')
        for tr in all_trs[1:]:
            item = ProxyIpItem()
            item['ip'] = tr.xpath('td[2]/text()').extract_first()
            item['port'] = tr.xpath('td[3]/text()').extract_first()
            item['ip_type'] = tr.xpath('td[6]/text()').extract_first()
            item['ip_speed'] = tr.xpath('td[7]/div/@title').extract_first()
            if item['ip_speed']:
                item['ip_speed'] = float(item['ip_speed'].split(u'秒')[0])
            item['ip_alive'] = tr.xpath('td[9]/text()').extract_first()

            http_url = "https://www.amazon.com/"
            proxy_url = "{2}://{0}:{1}".format(item['ip'], item['port'], str(item['ip_type']).lower())
            try:
                proxy_dict = {
                    "http": proxy_url,
                }
                proxy_response = requests.get(http_url, proxies=proxy_dict)
            except Exception as e:
                pass
            else:
                code = proxy_response.status_code
                if code >= 200 and code < 300:
                    check = ProxyIp.objects.filter(ip=item['ip'], port=item['port'])
                    if not check:
                        yield item
        next_page = response.css('div.pagination a.next_page::attr("href")').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
