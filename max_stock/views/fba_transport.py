# -*- coding: utf-8 -*-
import os,json
import xlrd
import time
import threading
import itertools
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import KitSkus,Sfps,Thresholds,WarehouseStocks,SfpTemps
from django.http import StreamingHttpResponse
from maxlead import settings

@csrf_exempt
def fba_transport(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    data = {
        'title': "FBA Transport",
        'user': user
    }
    return render(request, "Stocks/sfp/fba_transport.html", data)

@csrf_exempt
def import_fba_trans(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        myfiles = request.FILES.getlist('myfiles', '')
        if not myfiles:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}), content_type='application/json')
        for val in myfiles:
            file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'fba_transport', val.name)
            f = open(file_path, 'wb')
            for chunk in val.chunks():
                f.write(chunk)
            f.close()
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully!'}), content_type='application/json')

@csrf_exempt
def run_fba_trans(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'fba_transport')
    files = os.listdir(file_path)
    if len(files) != 1:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'文件不存在/正在运行~'}), content_type='application/json')
    xlsx_file = files[0]
    work_path = settings.STOCHS_SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    cmd_str = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=fatl1_spider -d xlsx_file=%s' % xlsx_file
    os.popen(cmd_str)
    os.chdir(settings.ROOT_PATH)
    return HttpResponse(json.dumps({'code': 1, 'msg': 'Running~'}), content_type='application/json')

@csrf_exempt
def init_fba_transport(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'fba_transport')
    files = os.listdir(file_path)
    if not files:
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully~'}), content_type='application/json')
    for val in files:
        path = os.path.join(file_path, val)
        os.remove(path)
    return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully~'}), content_type='application/json')