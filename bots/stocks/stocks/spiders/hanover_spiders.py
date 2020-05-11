# -*- coding: utf-8 -*-
import scrapy
import time
import MySQLdb
from sshtunnel import SSHTunnelForwarder
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from maxlead_res.bots.stocks.stocks import settings

class HanoverSpider(scrapy.Spider):
    name = "hanover_spider"

    msg_str1 = "complete\n"
    start_urls = [
        'http://www.telescoassoc.com/prod/hnv/transform.aspx?_h=go&_md=vwInventory&_tpl=vwInventoryList.xsl&_gt=-1&_gs=200&rhash=5adab926c2b523c494&_ha=gmv'
    ]
    sku_list = []
    log_id = None

    def __init__(self, *args, **kwargs):
        super(HanoverSpider, self).__init__(*args, **kwargs)
        self.server = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),  # B机器的配置
            ssh_password=settings.SSH_PASSWORD,
            ssh_username=settings.SSH_USER,
            remote_bind_address=(settings.MYSQL_HOST, settings.MYSQL_PORT))  # A机器的配置
        self.server.start()
        self.conn = MySQLdb.connect(host='127.0.0.1',  # 此处必须是是127.0.0.1
                                    port=self.server.local_bind_port,
                                    user=settings.MYSQL_USER,
                                    passwd=settings.MYSQL_PASSWORD,
                                    db=settings.MYSQL_DB_NAME)
        self.db_cur = self.conn.cursor()
        check_sql = "select id from mmc_spider_status where warehouse='Hanover'"
        status = self.db_cur.execute(check_sql)
        sql = "insert into mmc_spider_status (warehouse, status) values('Hanover',1)"
        if status > 0:
            sql = "update mmc_spider_status set status=1 where warehouse='Hanover'"
        self.db_cur.execute(sql)
        self.conn.commit()

    def parse(self, response):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(800, 800))
            display.start()
            firefox_options = Options()
            firefox_options.add_argument('-headless')
            firefox_options.add_argument('--disable-gpu')
            driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH)
            driver.get(response.url)
            driver.implicitly_wait(100)
            elem_code = driver.find_elements_by_id('WarehouseCode')
            elem_acode = driver.find_elements_by_id('AccountCode')
            elem_name = driver.find_elements_by_id('UserName')
            elem_pass = driver.find_elements_by_id('Password')
            btn_login = driver.find_elements_by_css_selector('input[name="Login"]')

            if elem_code:
                elem_code[0].send_keys('03')
            if elem_acode:
                elem_acode[0].send_keys('001862')
            if elem_name:
                elem_name[0].send_keys('MAXLEAD')
            if elem_pass:
                elem_pass[0].send_keys('1202HXML')
            btn_login[0].click()
            driver.implicitly_wait(100)
            time.sleep(5)
            total_page = driver.find_elements_by_css_selector('#navigationTR nobr')[0].text
            total_page = int(total_page.split(' ')[-1])

            for i in range(total_page):
                try:
                    res = driver.find_elements_by_css_selector('#ViewManyListTable tr')
                    elem = driver.find_element_by_id('MetaData')
                    elem.click()
                    res.pop(0)
                    for val in res:
                        td_re = val.find_elements_by_tag_name('td')
                        if td_re:
                            sku = td_re[0].text
                            warehouse = 'Hanover'
                            if td_re[3].text and not td_re[3].text == ' ':
                                qty = td_re[3].text
                                qty = qty.replace(',','')
                            else:
                                qty = 0

                            values = (warehouse, sku, qty)
                            sql = "insert into mmc_stocks (warehouse, sku, qty) values (%s, %s, %s)"
                            self.db_cur.execute(sql, values)
                    if i < total_page:
                        elem_next_page = driver.find_elements_by_id('Next')
                        if elem_next_page:
                            elem_next_page[0].click()
                            driver.implicitly_wait(100)
                except:
                    continue
            self.conn.commit()
            sql = "update mmc_spider_status set status=3, description='' where warehouse='Hanover'"
            self.db_cur.execute(sql)
            self.conn.commit()
        except Exception as e:
            values = (e,)
            sql = "update mmc_spider_status set status=2, description=%s where warehouse='Hanover'"
            self.db_cur.execute(sql, values)
            self.conn.commit()
        self.db_cur.close()
        self.conn.close()
        self.server.close()
        try:
            driver.refresh()
            driver.switch_to.alert.accept()
            driver.implicitly_wait(100)
        except:
            pass
        display.stop()
        driver.quit()

