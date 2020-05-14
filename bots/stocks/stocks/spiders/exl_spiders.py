# -*- coding: utf-8 -*-
import scrapy,os
from datetime import *
import time
import xlrd
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from maxlead_res.bots.stocks.stocks import settings

class ExlSpider(scrapy.Spider):
    name = "exl_spider"

    def start_requests(self):
        try:
            check_sql = "select id from mmc_spider_status where warehouse='3pl'"
            status = self.db_cur.execute(check_sql)
            sql = "insert into mmc_spider_status (warehouse, status) values('3pl',1)"
            if status > 0:
                sql = "update mmc_spider_status set status=1 where warehouse='3pl'"
            self.db_cur.execute(sql)
            self.conn.commit()

            url = 'https://secure-wms.com/smartui/?tplguid={073abe7b-9d71-414d-9933-c71befa9e569}'

            # FormRequest 是Scrapy发送POST请求的方法
            yield scrapy.FormRequest(
                url=url,
                callback=self.parse_page
            )
        except Exception as e:
            sql = "update mmc_spider_status set status=2 where warehouse='3pl'"
            self.db_cur.execute(sql)
            self.conn.commit()

    def parse_page(self, response):
        items = []
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(800, 800))
            display.start()
            profile = webdriver.FirefoxProfile()
            down_path = os.path.join(settings.DOWNLOAD_DIR, 'mmc_3pl')
            profile.set_preference('browser.download.dir', down_path)  # 现在文件存放的目录
            profile.set_preference('browser.download.folderList', 2)
            profile.set_preference('browser.download.manager.showWhenStarting', False)
            profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, '
                                                 'text/csv,application/x-msexcel,application/x-excel,application/excel,application/vnd.ms-excel')
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
            firefox_options.add_argument('-headless')
            firefox_options.add_argument('--disable-gpu')
            driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH, firefox_profile=profile)
            url = response.url
            driver.get(url)
            time.sleep(3)
            elem_name = driver.find_elements_by_id('login')
            elem_pass = driver.find_elements_by_id('password')
            btn_login = driver.find_elements_by_css_selector('button[type="submit"]')
            # sel_stock = driver.find_elements_by_id('StockStatusViewer__ctl1__ctl5__ctl0')

            # if type == 'myweb':
            #     if elem_name:
            #         elem_name[0].send_keys('Dteng')
            #     if elem_pass:
            #         elem_pass[0].send_keys('Tr@d3')
            # else:
            if elem_name:
                elem_name[0].send_keys('Intybot')
            if elem_pass:
                elem_pass[0].send_keys('7G1#AJjX')
            btn_login[0].click()
            driver.implicitly_wait(100)
            driver.get('https://secure-wms.com/WebUI/V1/V1Link/StockStatusReport.aspx')
            driver.implicitly_wait(100)
            time.sleep(3)
            close_guide = driver.find_elements_by_css_selector('#pendo-guide-container>button')
            if close_guide:
                print('---------------Click f65b1092!!!!')
                close_guide[0].click()
            list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
            list_rows.pop(0)
            list_rows.pop(-1)
            if list_rows:
                length = len(list_rows)
                for i in range(0, length):
                    try:
                        if not i == 0:
                            try:
                                driver.refresh()
                                driver.switch_to.alert.accept()
                                driver.implicitly_wait(100)
                            except:
                                pass
                            time.sleep(3)
                            driver.get('https://secure-wms.com/WebUI/V1/V1Link/StockStatusReport.aspx')
                            driver.implicitly_wait(100)
                            time.sleep(3)
                            list_rows = driver.find_elements_by_css_selector('#CustomerFacilityGrid_div-rows>span')
                            list_rows.pop(0)
                            list_rows.pop(-1)
                        warehouse_type = list_rows[i].find_elements_by_class_name('aw-column-0')
                        warehouse_name = list_rows[i].find_elements_by_class_name('aw-column-1')
                        warehouse_type_name = warehouse_type[0].text
                        if warehouse_name:
                            warehouse_name = warehouse_name[0].text
                        if warehouse_type_name in self.stock_names and warehouse_name and warehouse_name != 'ROL':
                            list_rows[i].find_element_by_tag_name('span').click()
                            btn_runreport = driver.find_elements_by_id('btnRunRpt')
                            if btn_runreport:
                                btn_runreport[0].click()
                                driver.implicitly_wait(100)
                                shutil.rmtree(down_path)
                                os.mkdir(down_path)
                            tb_time = 0
                            while 1:
                                table_re = driver.find_elements_by_id("StockStatusViewer")
                                try:
                                    if not table_re:
                                        driver.refresh()
                                        driver.switch_to.alert.accept()
                                        driver.implicitly_wait(100)
                                except:
                                    pass
                                time.sleep(10)
                                tb_time += 10
                                try:
                                    Select(driver.find_element_by_id("StockStatusViewer__ctl1__ctl5__ctl0")).select_by_value('EXCELOPENXML')
                                    driver.find_element_by_id("StockStatusViewer__ctl1__ctl5__ctl1").click()
                                    break
                                except:
                                    if tb_time > 40:
                                        break
                                    print('Error Element!')

                            time.sleep(20)
                            files = os.listdir(down_path)
                            if files:
                                f_path = os.path.join(down_path, files[0])
                                data = xlrd.open_workbook(f_path)  # 打开fname文件
                                data.sheet_names()  # 获取xls文件中所有sheet的名称
                                table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
                                nrows = table.nrows
                                if warehouse_name == 'Exchange Logistics':
                                    warehouse_name = 'EXL'
                                else:
                                    warehouse_name = 'TFD'
                                for i in range(nrows):
                                    try:
                                        i = i+7
                                        if i >= nrows:
                                            break
                                        item = {}
                                        item['sku'] = table.cell_value(i, 0,)
                                        if len(item['sku']) > 225:
                                            continue
                                        if item['sku']:
                                            item['warehouse'] = warehouse_name
                                            if table.cell_value(i, 11,) and not table.cell_value(i, 11,) == ' ':
                                                item['qty'] = table.cell_value(i, 11,)
                                                item['qty'] = int(item['qty'])
                                            else:
                                                item['qty'] = 0
                                            items.append(item)
                                    except:
                                        continue
                    except:
                        close_guide = driver.find_elements_by_css_selector('#pendo-guide-container>button')
                        if close_guide:
                            print('---------------Click f65b1092!!!!')
                            close_guide[0].click()
                        continue

            try:
                try:
                    driver.refresh()
                    driver.switch_to.alert.accept()
                    driver.implicitly_wait(100)
                except:
                    pass
                display.stop()
                driver.quit()
            except Exception as e:
                print(e)
        except Exception as e:
            values = (e,)
            sql = "update mmc_spider_status set status=2, description=%s where warehouse='3pl'"
            self.db_cur.execute(sql, values)
            self.conn.commit()

        try:
            for i, val in enumerate(items, 0):
                try:
                    for n, v in enumerate(items, 0):
                        if v['sku'] == val['sku'] and not i == n and  val['warehouse'] == v['warehouse']:
                            val['qty'] = int(v['qty']) + int(val['qty'])
                            del items[n]
                    values = (val['warehouse'], val['sku'], val['qty'])
                    sql = "insert into mmc_stocks (warehouse, sku, qty) values (%s, %s, %s)"
                    self.db_cur.execute(sql, values)
                except:
                    continue
            self.conn.commit()
            sql = "update mmc_spider_status set status=3, description='' where warehouse='3pl'"
            self.db_cur.execute(sql)
            self.conn.commit()
        except Exception as e:
            values = (e,)
            sql = "update mmc_spider_status set status=2, description=%s where warehouse='3pl'"
            self.db_cur.execute(sql, values)
            self.conn.commit()




