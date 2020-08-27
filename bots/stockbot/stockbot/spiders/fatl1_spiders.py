# -*- coding: utf-8 -*-
import scrapy,os
import xlrd
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from maxlead import settings as max_settings
from max_stock.models import FbaTransportTask

class Fatl1Spider(scrapy.Spider):
    name = "fatl1_spider"
    start_urls = [
        'https://www.amazon.com/dp/B01FBQHEC4/ref=sr_1_14?ie=UTF8&qid=1598432255&sr=1-14&keywords=B01FBQHEC4&th=1&psc=1&aid=B01FBQHEC4'
    ]

    def __init__(self, xlsx_file=None, *args, **kwargs):
        super(Fatl1Spider, self).__init__(*args, **kwargs)
        if xlsx_file:
            self.xlsx_file = xlsx_file

    def parse(self, response):
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("permissions.default.image", 2)
        profile.set_preference("network.http.use-cache", False)
        profile.set_preference("browser.cache.memory.enable", False)
        profile.set_preference("browser.cache.disk.enable", False)
        profile.set_preference("browser.sessionhistory.max_total_viewers", 3)
        profile.set_preference("network.dns.disableIPv6", True)
        profile.set_preference("Content.notify.interval", 750000)
        profile.set_preference("content.notify.backoffcount", 3)
        profile.set_preference("network.http.pipelining", True)
        profile.set_preference("network.http.proxy.pipelining", True)
        profile.set_preference("network.http.pipelining.maxrequests", 32)

        firefox_options = Options()
        # firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)
        driver.get(response.url)
        elem_name = driver.find_elements_by_name('uid')
        elem_pass = driver.find_elements_by_name('pwd')
        btn_login = driver.find_elements_by_class_name('btn-success')

        if elem_name:
            elem_name[0].send_keys('tradeforce')
        if elem_pass:
            elem_pass[0].send_keys('1202@hxml')
        btn_login[0].click()
        driver.implicitly_wait(100)
        driver.get('http://us.hipacking.com/member/instock/stock.html')
        driver.implicitly_wait(100)
        # btn_msg = driver.find_elements_by_class_name('layui-layer-btn0')
        # if btn_msg:
        #     btn_msg[0].click()

        xlsx_path = os.path.join(max_settings.BASE_DIR, max_settings.DOWNLOAD_URL, 'fba_transport', self.xlsx_file)
        data = xlrd.open_workbook(xlsx_path)  # 打开fname文件
        data.sheet_names()  # 获取xls文件中所有sheet的名称
        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
        nrows = table.nrows
        num = 'start'
        dec_str = ''
        skus = []
        for i in range(nrows):
            try:
                if i + 1 < nrows:
                    sku = table.cell_value(i + 1, 1, )
                    qty = int(table.cell_value(i + 1, 2, ))
                    if i + 1 == 1:
                        whs = table.cell_value(i + 1, 0, )
                        key_el = driver.find_element_by_id('keyword')
                        key_el.send_keys(sku)
                        if whs == 'ONT':
                            driver.find_elements_by_css_selector('#avdSearch ~ button')[1].click()
                        else:
                            driver.find_elements_by_css_selector('#avdSearch ~ button')[0].click()
                        driver.implicitly_wait(100)
                        time.sleep(3)
                        sku_tr = driver.find_elements_by_css_selector('.table>tbody>tr')
                        if not sku_tr:
                            dec_str += '%s;' % sku
                            if nrows > 2:
                                driver.find_element_by_id('add_productA').click()
                                driver.implicitly_wait(100)
                            continue
                        else:
                            if len(sku_tr) > 1:
                                for val in sku_tr:
                                    sku_tr_name = val.find_element_by_css_selector('td:nth-of-type(4)').text
                                    if sku_tr_name == sku:
                                        chc_tr = val
                                        break
                            else:
                                chc_tr = sku_tr[0]
                            chcBox = chc_tr.find_element_by_tag_name('input')
                            qty1 = driver.find_element_by_css_selector('.table>tbody>tr>td:nth-of-type(10)').text
                            if int(qty1) < int(qty):
                                dec_str += 'sku:%s库存不足,数据未处理.' % sku
                                if nrows > 2:
                                    driver.find_element_by_id('add_productA').click()
                                    driver.implicitly_wait(100)
                                break
                            num = 0
                            chcBox.click()
                        fba_trspot = driver.find_elements_by_css_selector('.page-nav>button')
                        fba_trspot[1].click()
                        driver.implicitly_wait(100)
                        skus.append({
                            'sku' : sku,
                            'qty' : qty
                        })
                        if nrows > 2:
                            driver.find_element_by_id('add_productA').click()
                            driver.implicitly_wait(100)
                    else:
                        ifram_ti = 0
                        while 1:
                            try:
                                if ifram_ti > 200:
                                    break
                                iframe1 = driver.find_elements_by_tag_name('iframe')
                                if iframe1:
                                    driver.switch_to.frame(iframe1[0])
                                    driver.implicitly_wait(100)
                                    time.sleep(3)
                                    break
                            except:
                                ifram_ti += 3
                                time.sleep(3)
                        key_el = driver.find_element_by_id('keyword')
                        serc_el = driver.find_element_by_id('avdSearch')
                        key_el.clear()
                        key_el.send_keys(sku)
                        serc_el.click()
                        driver.implicitly_wait(100)
                        time.sleep(3)
                        sku_tr = driver.find_elements_by_css_selector('.table>tbody>tr')
                        if not sku_tr:
                            dec_str += '%s;' % sku
                            if nrows > 2 and i < (range(nrows)[-1] - 1):
                                driver.find_element_by_id('add_productA').click()
                                driver.implicitly_wait(100)
                            continue
                        else:
                            if len(sku_tr) > 1:
                                for val in sku_tr:
                                    sku_tr_name = val.find_element_by_css_selector('td:nth-of-type(4)').text
                                    if sku_tr_name == sku:
                                        chc_tr = val
                                        break
                            else:
                                chc_tr = sku_tr[0]
                            chcBox = chc_tr.find_element_by_tag_name('input')

                            qty1 = driver.find_element_by_css_selector('.table>tbody>tr>td:nth-of-type(8)').text
                            if int(qty1) < int(qty):
                                dec_str += 'sku:%s库存不足;' % sku
                                driver.switch_to.default_content()
                                driver.implicitly_wait(100)
                                time.sleep(3)
                                close_a = driver.find_element_by_class_name(
                                    'layui-layer-setwin').find_element_by_tag_name('a')
                                close_a.click()
                                if nrows > 2 and i < (range(nrows)[-1] - 1):
                                    driver.find_element_by_id('add_productA').click()
                                    driver.implicitly_wait(100)
                                continue
                            if num == 'start':
                                num = 0
                            else:
                                num += 1
                            chcBox.click()
                        driver.switch_to.default_content()
                        driver.implicitly_wait(100)
                        time.sleep(3)
                        close_a = driver.find_element_by_class_name('layui-layer-setwin').find_element_by_tag_name('a')
                        close_a.click()
                        skus.append({
                            'sku': sku,
                            'qty': qty
                        })
                        if nrows > 2 and i < (range(nrows)[-1] - 1):
                            driver.find_element_by_id('add_productA').click()
                            driver.implicitly_wait(100)
                if i % 5 == 0 and i != 0:
                    try:
                        driver.refresh()
                        driver.implicitly_wait(100)
                        if nrows > 2 and i < (range(nrows)[-1] - 1):
                            driver.find_element_by_id('add_productA').click()
                            driver.implicitly_wait(100)
                    except:
                        pass
            except:
                dec_str += '%s;' % sku
                continue
        prdut_trs = driver.find_elements_by_css_selector('.product-table>tbody>tr')
        for i,val in enumerate(prdut_trs):
            val.find_elements_by_tag_name('input')[1].clear()
            val.find_elements_by_tag_name('input')[0].send_keys(skus[i]['sku'])
            val.find_elements_by_tag_name('input')[1].send_keys(skus[i]['qty'])
        try:
            driver.find_element_by_id('submit').click()
        except:
            driver.switch_to.default_content()
            driver.implicitly_wait(100)
            time.sleep(3)
            close_a = driver.find_element_by_class_name('layui-layer-setwin').find_element_by_tag_name('a')
            close_a.click()
            driver.find_element_by_id('submit').click()
        driver.implicitly_wait(100)
        done_time = 0
        while 1:
            try:
                che_num = driver.find_element_by_id('number').get_attribute("value")
                break
            except:
                done_time += 3
                if done_time > 200:
                    break
                time.sleep(3)
        os.remove(xlsx_path)
        obj = FbaTransportTask.objects.filter(file_path=xlsx_path)
        if obj:
            obj.update(status='Done')
            if dec_str:
                obj.update(description=dec_str)
        # display.stop()
        driver.quit()
