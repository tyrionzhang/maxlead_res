# -*- coding: utf-8 -*-  
from selenium import webdriver
from scrapy.http import HtmlResponse
import requests,time,random
from bots.maxlead_scrapy.maxlead_scrapy import settings
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from maxlead_site.models import Questions,Answers

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
