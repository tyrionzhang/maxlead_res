# -*- coding: utf-8 -*-
import scrapy,os
from scrapy.http import Request, FormRequest
from bots.stockbot.stockbot.items import WarehouseStocksItem
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from maxlead import settings as max_settings
from django.core.mail import send_mail

class TwuSpider(scrapy.Spider):
    name = "twu_spider"
    sku_list = []
    msg_str1 = 'complete\n'

    def __init__(self, username=None, *args, **kwargs):
        super(TwuSpider, self).__init__(*args, **kwargs)
        file_name = 'userSkus_txt.txt'
        if username:
            file_name = 'userSkus_txt_%s.txt' % username
        file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, file_name)
        with open(file_path, "r") as f:
            sku_list = f.read()
            f.close()
        if sku_list:
            self.sku_list = eval(sku_list)

    def start_requests(self):
        return [Request("http://www.thewarehouseusadata.com/maxlead/inventory.php", meta={'cookiejar': 1}, callback=self.post_login)]

    def post_login(self, response):
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
                                              'username': 'Lead2MAX',
                                              'password': 'dwf@twu415!'
                                          },
                                          callback=self.parse_page,
                                          dont_filter=True
                                          )]


    def parse_page(self, response):
        res = response.css('article')[0].css('table[width="100%"]>tr')
        if res:
            fields = res[1].css('td::text').extract()
            res.pop(1)
            res.pop(0)
            fields.pop(0)
            msg_str2 = ''
            file_path = os.path.join(max_settings.BASE_DIR, max_settings.THRESHOLD_TXT, 'threshold_txt.txt')
            for val in res:
                item = WarehouseStocksItem()
                items = val.css('td::text').extract()
                if items:
                    item['sku'] = items[0]
                    item['warehouse'] = 'TWU'
                    item['is_new'] = 1
                    if items[11] and not items[11] == ' ':
                        item['qty'] = items[11]
                        item['qty'] = item['qty'].replace(',', '')
                    else:
                        item['qty'] = 0
                    yield item
                    threshold = Thresholds.objects.filter(sku=item['sku'], warehouse=item['warehouse'])
                    user = SkuUsers.objects.filter(sku=item['sku'])
                    if threshold and threshold[0].threshold >= int(item['qty']):
                        if user:
                            msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (user[0].user.email,
                                                item['sku'], item['warehouse'],item['qty'], threshold[0].threshold)

            if not os.path.isfile(file_path):
                with open(file_path, "w+") as f:
                    f.close()
            with open(file_path, "r+") as f:
                old = f.read()
                f.seek(0)
                f.write(self.msg_str1)
                f.write(old)
                f.write(msg_str2)
                f.close()

            with open(file_path, "r") as f:
                msg1 = f.readline()
                msg2 = f.readline()
                msg3 = f.readline()
                msg4 = f.readline()
                if msg1 == 'complete\n' and msg2 == 'complete\n' and msg3 == 'complete\n' and msg4 == 'complete\n':
                    msg_line = f.read()
                    if msg_line:
                        msg_line = msg_line.split('|')
                        msg_line.pop()
                        all_msg = ''
                        subject = 'Maxlead库存预警'
                        from_email = max_settings.EMAIL_HOST_USER

                        msg = {}
                        for i, val in enumerate(msg_line, 1):
                            val = val.split('=>')
                            msg_res_str = val[1]
                            for n, v in enumerate(msg_line, 1):
                                v = v.split('=>')
                                if not n == i and val[0] == v[0]:
                                    msg_res_str += v[1]
                            msg.update({val[0]: msg_res_str})
                        for key in msg:
                            send_mail(subject, msg[key], from_email, [key], fail_silently=False)
                        send_mail(subject, all_msg, from_email, ['shipping.gmi@gmail.com'], fail_silently=False)
                    f.close()
                    os.remove(file_path)