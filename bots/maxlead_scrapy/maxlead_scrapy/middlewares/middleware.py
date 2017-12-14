# -*- coding: utf-8 -*-  
from selenium import webdriver
from scrapy.http import HtmlResponse
import requests,time,os
from bots.maxlead_scrapy.maxlead_scrapy import settings
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from maxlead_site.models import Questions,Answers

class JavaScriptMiddleware(object):
    driver = webdriver.PhantomJS(executable_path='C:\\Users\\asus\\node_modules\\phantomjs\\lib\\phantom\\bin\\phantomjs.exe')

    def _save_qa_action(self,url,votes):
        question = self.driver.find_element_by_class_name('askAnswersAndComments').text
        res_asin = url.split('/')
        asin_id = res_asin[6]
        votes = votes
        asked = self.driver.find_element_by_css_selector('.a-spacing-base .a-text-left').text
        qa_data = Questions(question=question, asin=asin_id, asked=asked, votes=votes)
        qa_data.id
        qa_data.save()
        qa_data.id
        try:
            answers = self.driver.find_elements_by_css_selector('.askAnswersAndComments>.a-section')
            if answers:
                for asw in answers:
                    person = asw.find_element_by_class_name('a-color-tertiary').text
                    answer = asw.find_element_by_tag_name('span').text
                    answer_data = Answers(question=qa_data, person=person, answer=answer)
                    answer_data.id
                    answer_data.save()
                    answer_data.id
        except (IOError, ZeroDivisionError):
            print(IOError)


    def process_request(self, request, spider):
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
            qa_res = self.driver.find_elements_by_css_selector('.askInlineWidget>.askTeaserQuestions>.a-spacing-base')
            vote_el = self.driver.find_elements_by_css_selector('.askInlineWidget .voteAjax')
            votes_list = []
            if vote_el:
                for val in vote_el:
                    val.is_enabled()
                    votes_list.append(val.find_element_by_class_name('count').text)
            if qa_res:
                for i in range(len(qa_res)):
                    qa_el = self.driver.find_elements_by_css_selector('.askInlineWidget>.askTeaserQuestions>.a-spacing-base')
                    cl_el = qa_el[i].find_element_by_css_selector('.a-spacing-base .a-link-normal')
                    cl_el.click()
                    time.sleep(2)
                    # r = requests.get(url, headers=headers)
                    # time.sleep(5)
                    #
                    # body = r.content
                    self._save_qa_action(url=url,votes=votes_list[i])
                    self.driver.back()
                    time.sleep(8)
            self.driver.quit()

            return HtmlResponse(url, encoding='utf-8', status=200, body=body)
        except (IOError ,ZeroDivisionError):
            print(IOError)
