import os,sched
from datetime import *
import queue
import threading
import time
from django.http import HttpResponseRedirect
from django.shortcuts import render
from maxlead_site.views.app import App
from maxlead import settings
from max_stock.models import SkuUsers,StockLogs,WarehouseStocks
from django.http import HttpResponse

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def _set_user_sku(request=None):
    sku_list = []
    if request:
        user = App.get_user_info(request)
    user_skus = SkuUsers.objects.filter().all()
    if request and not user.user.is_superuser:
        user_skus = user_skus.filter(user=user.user)
    if user_skus:
        for val in user_skus:
            sku_list.append(val.sku)
        file_path = os.path.join(settings.BASE_DIR, settings.THRESHOLD_TXT, 'userSkus_txt.txt')
        with open(file_path, "w+") as f:
            sku_list = str(sku_list)
            f.write(sku_list)
            f.close()
    return True

class perform_command_que(threading.Thread):
    def __init__(self, t_name, queue):
        threading.Thread.__init__(self,name=t_name)
        self.data = queue
        self.t_name = t_name

    def run(self):
        work_path = settings.STOCHS_SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')

        cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=twu_spider'
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=hanover_spider'
        cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=exl_spider'
        # cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=exl1_spider'
        os.popen(cmd_str2)
        os.popen(cmd_str1)
        os.popen(cmd_str3)
        # os.popen(cmd_str4)
        print('%s:%s finished!' % (time.time(), self.getName()))
        os.chdir(settings.ROOT_PATH)

def run_command_queue():
    spiders_time = "%.1f" % settings.STOCHS_TIME
    t = threading.Timer(float(spiders_time), run_command_queue)
    _set_user_sku()
    q = queue.Queue()

    tname = 'stocks_done'
    reviews = perform_command_que(tname, q)
    reviews.start()
    reviews.join()
    t.start()

def stock_spiders(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    type = request.GET.get('type','')
    if type == 'now':
        _set_user_sku(request)
        q = queue.Queue()

        tname = 'stocks_done'
        reviews = perform_command_que(tname, q)
        reviews.start()
        reviews.join()
        msg_str = 'Spiders is runing!'
    else:
        t = threading.Timer(54000.0, run_command_queue)
        # 持续运行，直到计划时间队列变成空为止
        t.start()
        time_str = datetime.now() +  timedelta(seconds = 54000)
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
    WarehouseStocks.objects.filter().all().delete()
    StockLogs.objects.filter().all().delete()
    return HttpResponse(request, 'Spiders is runing!Time:%s' % datetime.now())