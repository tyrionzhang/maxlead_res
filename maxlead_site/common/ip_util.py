# -*- coding: utf-8 -*-
import random,requests
from maxlead_site.models import ProxyIp

# ip的管理类
class IPUtil(object):
    def get_random_ip(self):
        # 从数据库中随机获取一个可用的ip
        n = 10
        ip_count = ProxyIp.objects.count()
        if ip_count:
            i = ip_count - n
            if i < 0:
                i = ip_count
            count = random.randint(0, i)
            rand_ids = ProxyIp.objects.all()[count : count + n]
            for ip_info in rand_ids:
                ip = ip_info.ip
                port = ip_info.port
                ip_type = ip_info.ip_type

                judge_re = self.judge_ip(ip, port, ip_type)
                if judge_re:
                    return "{2}://{0}:{1}".format(ip, port, str(ip_type).lower())
                else:
                    return self.get_random_ip()

    def judge_ip(self, ip, port, ip_type):
        # 判断ip是否可用，如果通过代理ip访问百度，返回code200则说明可用
        # 若不可用则从数据库中删除
        print ('begin judging ---->', ip, port, ip_type)
        http_url = "https://www.amazon.com/"
        proxy_url = "{2}://{0}:{1}".format(ip, port, str(ip_type).lower())
        try:
            proxy_dict = {
                "http": proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print ("invalid ip and port,cannot connect amazon")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                self.delete_ip(ip)
                return False

    # noinspection SqlDialectInspection
    def delete_ip(self, ip):
        # 从数据库中删除无效的ip
        delete_sql = ProxyIp.objects.filter(ip=ip)
        delete_sql.delete()
        return True