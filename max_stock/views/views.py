import os,sched,calendar
from datetime import *
import queue
import json
import threading
import time
import requests
from django.http import HttpResponseRedirect
from django.shortcuts import render
from maxlead_site.views.app import App
from maxlead import settings
from maxlead_site.models import UserProfile
from max_stock.models import SkuUsers,StockLogs,WarehouseStocks,OldOrderItems,OrderItems,EmailTemplates,UserEmailMsg,SpidersLogs
from max_stock.models import KitSkus
from django.http import HttpResponse
from max_stock.views.stocks import covered_stocks
from maxlead_site.common.common import kill_pid_for_name

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)
week_day = {
    'monday':'MONDAY',
    'tuesday':'TUESDAY',
    'wednesday':'WEDNESDAY',
    'thursday':'THURSDAY',
    'saturday':'SATURDAY',
    'sunday':'SUNDAY',
}
def getNextSaturday():
    today = date.today()
    oneday = timedelta(days = 1)
    m1 = calendar.SATURDAY
    while today.weekday() != m1:
        today += oneday
    re = today.strftime('%Y-%m-%d')
    return re

def _set_user_sku(request=None):
    sku_list = []
    file_name = 'userSkus_txt.txt'
    if request:
        user = App.get_user_info(request)
    user_skus = SkuUsers.objects.filter().all()
    if request and not user.user.is_superuser:
        user_skus = user_skus.filter(user=user.user)
        file_name = 'userSkus_txt_%s.txt' % user.user.username
    if user_skus:
        for val in user_skus:
            sku_list.append(val.sku)
        file_path = os.path.join(settings.BASE_DIR, settings.THRESHOLD_TXT, file_name)
        with open(file_path, "w+") as f:
            sku_list = str(sku_list)
            f.write(sku_list)
            f.close()
    return True

class perform_command_que(threading.Thread):
    stock_names = ['ml', 'match', 'parts']

    def __init__(self, t_name, queue, request=None):
        threading.Thread.__init__(self,name=t_name)
        self.data = queue
        self.t_name = t_name
        self.username = ''
        if request:
            user = App.get_user_info(request)
            if not user.user.is_superuser:
                self.username = user.user.username

    def run(self):
        work_path = settings.STOCHS_SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')

        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=hanover_spider -d username=%s' % self.username
        cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=twu_spider -d username=%s' % self.username

        t = threading.Timer(270.0, self.run_atl_spider)
        t.start()
        t1 = threading.Timer(600.0, self.run_exl_spider)
        t1.start()

        os.popen(cmd_str1)
        os.popen(cmd_str2)
        print('%s:%s finished!' % (time.time(), self.getName()))
        os.chdir(settings.ROOT_PATH)

    def run_exl_spider(self):
        cmd_str = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=exl_spider'
        os.popen(cmd_str)

    def run_atl_spider(self):
        cmd_str5 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=zto_spider -d username=%s' % self.username
        cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=atl1_spider -d username=%s' % self.username
        os.popen(cmd_str5)
        time.sleep(300)
        os.popen(cmd_str4)

def run_command_queue():
    # time_now = datetime.now()
    # time_re = datetime.now() + timedelta(days=1)
    # time_saturday = '%s 05:00:00' % time_re.strftime('%Y-%m-%d')
    # time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M:%S')
    # t_re = (time_saturday - time_now).total_seconds()
    # spiders_time = "%.1f" % t_re
    t = threading.Timer(86400.0, run_command_queue)
    SlogsObj = SpidersLogs()
    SlogsObj.id
    SlogsObj.user_id = 1
    SlogsObj.start_time = datetime.now()
    SlogsObj.save()

    _set_user_sku()
    q = queue.Queue()

    tname = 'stocks_done'
    reviews = perform_command_que(tname, q)
    reviews.start()
    reviews.join()
    t.start()
    pass

def stock_spiders(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    type = request.GET.get('type','')
    if type == 'now':
        runLogs = SpidersLogs.objects.filter(is_done=0)
        if not runLogs:
            _set_user_sku(request)
            q = queue.Queue()

            tname = 'stocks_done'
            reviews = perform_command_que(tname, q, request)
            reviews.start()
            reviews.join()
            msg_str = u'爬虫已运行'
            SlogsObj = SpidersLogs()
            SlogsObj.id
            SlogsObj.user_id = user.user_id
            SlogsObj.start_time = datetime.now()
            SlogsObj.save()
        else:
            msg_str = u'更新正在进行...'
    else:
        time_now = datetime.now()
        time_re = datetime.now() + timedelta(days = 1)
        time_saturday = '%s 05:00:00' % time_re.strftime('%Y-%m-%d')
        time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M:%S')
        t_re = (time_saturday - time_now).total_seconds()
        t = threading.Timer(float('%.1f' % int(t_re)), run_command_queue)
        # 持续运行，直到计划时间队列变成空为止
        t.start()
        time_save_stocks = '%s 06:00:00' % time_re.strftime('%Y-%m-%d')
        time_save_stocks = datetime.strptime(time_save_stocks, '%Y-%m-%d %H:%M:%S')
        t_re = (time_save_stocks - time_now).total_seconds()
        save_stocks_t = threading.Timer(float('%.1f' % int(t_re)), task_save_stocks)
        # 持续运行，直到计划时间队列变成空为止
        save_stocks_t.start()
        time_str = datetime.now() +  timedelta(seconds = int(t_re))
        msg_str = 'Spiders will be runing!The time:%s' % time_str
    return render(request, "Stocks/spider/home.html", {'msg_str':msg_str})

def save_logs(data):
    logs = StockLogs()
    logs.id
    logs.user = data['user']
    logs.fun = data['fun']
    logs.description = data['description']
    res = logs.save()
    return True

def empty_data(request):
    UserEmailMsg.objects.filter().all().delete()
    return HttpResponse(request, 'Spiders is runing!Time:%s' % datetime.now())

def test(request):
    work_path = settings.STOCHS_SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')

    cmd_str2_test = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=email_spider'
    os.popen(cmd_str2_test)
    return render(request, "Stocks/spider/home.html", {'msg_str': 'Done!'})

def task_save_stocks():
    t = threading.Timer(86400.0, task_save_stocks)
    stocks = WarehouseStocks.objects.filter(is_new=1)
    user = UserProfile.objects.get(user_id=1)
    for val in stocks:
        re = {}
        re.update({
            'sku' : val.sku,
            'warehouse' : val.warehouse,
            'qty_new' : val.qty,
            'qty1' : val.qty1,
            'date' : val.created
        })
        try:
            covered_stocks(user.user, re, 'Auto save.')
        except:
            continue
    t.start()
    pass

def copy_stocks_of_pc():
    t = threading.Timer(86400.0, copy_stocks_of_pc)
    pc_obj = WarehouseStocks.objects.filter(warehouse='PC').order_by('-created')
    if pc_obj:
        sherch_date = pc_obj[0].created.strftime("%Y-%m-%d")
        stocks = WarehouseStocks.objects.filter(warehouse='PC', created__contains=sherch_date)
        querysetlist = []
        for val in stocks:
            try:
                querysetlist.append(WarehouseStocks(
                    sku= val.sku,
                    warehouse= 'PC',
                    qty1= val.qty1,
                    is_new= 0,
                    qty= val.qty
                ))
            except:
                continue
        if querysetlist:
            WarehouseStocks.objects.bulk_create(querysetlist)
    t.start()


def help_page(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    return render(request, "Stocks/users_sku/help_page.html")

def update_spiders_logs(name, is_done=0, log_id=None):

    if log_id:
        obj = SpidersLogs.objects.filter(id=log_id)
    else:
        obj = SpidersLogs.objects.filter(is_done=0)
    if obj:
        id = obj[0].id
        now_time = datetime.now().strftime("%m-%d %H:%M:%S")
        now_time1 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        des_str = obj[0].description + '%s的数据已拉取完毕,时间%s<br>' % (name, now_time)
        obj.update(description=des_str)
        if '3pl' in des_str:
            is_done = 1
        if is_done:
            obj.update(is_done=is_done, end_time=now_time1)
        return id

def kill_postgres_on_type():
    t = threading.Timer(86400.0, kill_postgres_on_type)
    kill_pid_for_name('postgres', select_type = 'SELECT')
    t.start()

def del_orders():
    t = threading.Timer(86400.0, del_orders)
    data = OrderItems.objects.filter(is_email=0)
    if data:
        data.delete()
    t.start()

def run_zto_spiders():
    t = threading.Timer(86400.0, run_zto_spiders)
    work_path = settings.STOCHS_SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    cmd_str5 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=zto_spider'
    os.popen(cmd_str5)
    os.chdir(settings.ROOT_PATH)
    t.start()

def check_spiders(new_log=None):
    if new_log:
        obj = SpidersLogs.objects.filter(id=new_log)
    else:
        date_now = datetime.now().strftime('%Y-%m-%d')
        obj = SpidersLogs.objects.filter(created__contains=date_now).order_by('-created')
    if obj:
        os.popen('killall -9 firefox')
        work_path = settings.STOCHS_SPIDER_URL
        des = obj[0].description
        spiders = []
        if 'ZTO' not in des:
            spiders.append('curl http://localhost:6800/schedule.json -d project=stockbot -d spider=zto_spider -d log_id=%s' % obj[0].id)
        if 'ATL' not in des:
            spiders.append('curl http://localhost:6800/schedule.json -d project=stockbot -d spider=atl1_spider -d log_id=%s' % obj[0].id)
        if 'Hanover' not in des:
            spiders.append('curl http://localhost:6800/schedule.json -d project=stockbot -d spider=hanover_spider -d log_id=%s' % obj[0].id)
        if 'TWU' not in des:
            spiders.append('curl http://localhost:6800/schedule.json -d project=stockbot -d spider=twu_spider -d log_id=%s' % obj[0].id)
        if '3pl' not in des:
            spiders.append('curl http://localhost:6800/schedule.json -d project=stockbot -d spider=exl_spider -d log_id=%s' % obj[0].id)
        if spiders:
            os.chdir(work_path)
            os.popen('scrapyd-deploy')
            for val in spiders:
                os.popen(val)
                time.sleep(300)
        os.chdir(settings.ROOT_PATH)
        os.popen('killall -9 firefox')

def get_kit_skus():
    headers = {
        'User-Agent' : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        'Authorization': 'NLAuth nlauth_account=5339579, nlauth_email=rudy.zhangwei@cdsht.cn, nlauth_signature=Maxlead123, nlauth_role=3'
    }
    url = 'https://5339579.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=376&deploy=1&start_date=%s&end_date=%s'
    kit_obj = KitSkus.objects.all().order_by('-created')
    start_date = '10/24/2019'
    if kit_obj:
        start_date = kit_obj[0].created.strftime("%m/%d/%Y")
    url = url % (start_date, datetime.now().strftime("%m/%d/%Y"))
    res = requests.get(url, headers=headers)
    res = json.loads(res.content.decode())
    querylist = []
    for val in res:
        try:
            che = KitSkus.objects.filter(kit=val['kit'])
            if che:
                che.update(sku=val['sku'])
            else:
                querylist.append(KitSkus(kit=val['kit'], sku=val['sku']))
        except:
            continue
    if querylist:
        KitSkus.objects.bulk_create(querylist)
