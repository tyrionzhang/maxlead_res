# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import xlrd
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from maxlead_res.bots.stocks.stocks import settings

class ZtoSpider(scrapy.Spider):
    name = "zto_spider"

    def start_requests(self):
        try:
            check_sql = "select id from mmc_spider_status where warehouse='zto'"
            self.db_cur.execute(check_sql)
            self.db_cur.fetchone()
            status = self.db_cur.rowcount
            sql = "insert into mmc_spider_status (warehouse, status) values('ZTO',1)"
            if status > 0:
                sql = "update mmc_spider_status set status=1 where warehouse='ZTO'"
            self.db_cur.execute(sql)
            self.conn.commit()

            url = 'https://fba3-us.zto.cn/stock'

            # FormRequest 是Scrapy发送POST请求的方法
            yield scrapy.FormRequest(
                url=url,
                callback=self.parse_page
            )
        except Exception as e:
            sql = "update mmc_spider_status set status=2 where warehouse='ZTO'"
            self.db_cur.execute(sql)
            self.conn.commit()

    def parse_page(self, response):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        profile = webdriver.FirefoxProfile()
        down_path = os.path.join(settings.DOWNLOAD_DIR, 'mmc_zto')
        profile.set_preference('browser.download.dir', down_path)  # 现在文件存放的目录
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, '
                               'text/csv,application/x-msexcel,application/x-excel,application/excel,application/vnd.ms-excel,application/x-download')

        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)
        driver.get(response.url)
        time.sleep(5)
        btn_export = False
        try:
            elem_name = driver.find_elements_by_name('username')
            elem_pass = driver.find_elements_by_name('password')
            btn_login = driver.find_element_by_id('sub-btn')

            if elem_name:
                elem_name[0].send_keys('ZTLO')
            if elem_pass:
                elem_pass[0].send_keys('123456')
            btn_login.click()
            driver.implicitly_wait(100)
            time.sleep(3)
            try:
                wrapper_btn = driver.find_elements_by_class_name('el-button--small')
                if wrapper_btn and wrapper_btn[1].is_displayed():
                    wrapper_btn[1].click()
            except:
                pass
            stock_li = driver.find_element_by_id('stock')
            stock_li.click()
            driver.implicitly_wait(100)
            time.sleep(3)
            waits = 0
            while 1:
                time.sleep(3)
                try:
                    btn_export = driver.find_element_by_css_selector('.text-right>button:nth-of-type(2)')
                    break
                except:
                    waits += 5
                    if waits > 120:
                        break
                    continue
            if btn_export:
                btn_export.click()
                time.sleep(20)
                files = os.listdir(down_path)
                if files:
                    f_path = os.path.join(down_path, files[0])
                    if os.path.isfile(f_path):
                        data = xlrd.open_workbook(f_path)  # 打开fname文件
                        data.sheet_names()  # 获取xls文件中所有sheet的名称
                        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
                        nrows = table.nrows
                        for i in range(1, nrows):
                            try:
                                if i >= nrows:
                                    break
                                sku = table.cell_value(i, 1, )
                                warehouse = 'ZTO'
                                qty = table.cell_value(i, 3, )
                                if qty:
                                    qty5 = int(table.cell_value(i, 5, ))
                                    if qty5:
                                        qty = int(qty) - qty5
                                else:
                                    qty = 0
                                qty_sql = "select id from mmc_stocks where commodity_repertory_sku='%s' and warehouse='%s'" % (
                                sku, warehouse)
                                self.db_cur.execute(qty_sql)
                                self.db_cur.fetchone
                                qty_re = self.db_cur.rowcount
                                values = (qty, sku, warehouse)
                                if qty_re > 0:
                                    sql = "update mmc_stocks set qty=%s where commodity_repertory_sku=%s and warehouse=%s"
                                else:
                                    sql = "insert into mmc_stocks (qty, commodity_repertory_sku, warehouse) values (%s, %s, %s)"
                                self.db_cur.execute(sql, values)
                            except:
                                continue
                        self.conn.commit()
                        sql = "update mmc_spider_status set status=3, description='' where warehouse='ZTO'"
                        self.db_cur.execute(sql)
                        self.conn.commit()
        except Exception as e:
            values = (str(e),)
            sql = "update mmc_spider_status set status=2, description=%s where warehouse='ZTO'"
            self.db_cur.execute(sql, values)
            self.conn.commit()
        try:
            driver.refresh()
            driver.switch_to.alert.accept()
            driver.implicitly_wait(100)
        except:
            pass
        shutil.rmtree(down_path)
        os.mkdir(down_path)
        display.stop()
        driver.quit()
