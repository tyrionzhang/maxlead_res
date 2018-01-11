# -*- coding: utf-8 -*-  
from selenium import webdriver
from scrapy.http import HtmlResponse
import requests,time,random
from bots.maxlead_scrapy.maxlead_scrapy import settings
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from scrapy import log
import logging
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
class JavaScriptMiddleware(object):
    driver = webdriver.PhantomJS(executable_path='C:\\Users\\asus\\node_modules\\phantomjs\\lib\\phantom\\bin\\phantomjs.exe')

    def process_request(self, request, spider):
        # thisip = random.choice(settings.IPPOOL)
        # print("this is ip:" + thisip["ipaddr"])
        # request.meta["proxy"] = "http://" + thisip["ipaddr"]
        dcap = dict(DesiredCapabilities.PHANTOMJS)  # 设置useragent
        dcap['phantomjs.page.settings.userAgent'] = settings.UA
        # user_agent = settings.UA
        # headers = {'User-Agent': user_agent}
        # driver = webdriver.Firefox()
        url = request.url
        try:
            self.driver.get(url)
            time.sleep(1)
            # self.driver.execute_script(js) # 可执行js，模仿用户操作。此处为将页面拉至最底端。
            body = self.driver.page_source
            # self.driver.save_screenshot('1.png')  # 截图保存
            # self.driver.find_element_by_id('dropdown_selected_size_name').click()
            # webdriver.ActionChains(self.driver).move_to_element() #鼠标移动

            return HtmlResponse(url, encoding='utf-8', status=200, body=body)
        except (IOError ,ZeroDivisionError):
            print(IOError)

class UserAgent(UserAgentMiddleware):
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 "
        "(KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 "
        "(KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 "
        "(KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 "
        "(KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 "
        "(KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 "
        "(KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 "
        "(KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 "
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 "
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]

    def __init__(self, user_agent=''):
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        if ua:
            log.msg('Current UserAgent: ' + ua, level=logging.DEBUG)
            request.headers.setdefault('User-Agent', ua)
