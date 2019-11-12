# -*- coding: utf-8 -*-
import os,json
import datetime
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import FbaTransportTask
from maxlead import settings

@csrf_exempt
def fba_transport(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    res = FbaTransportTask.objects.all().order_by('-id', '-created')
    for val in res:
        val.file_name = val.file_path.split('/')[-1]
    data = {
        'data': res,
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
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'fba_transport', myfiles[0].name.replace(' ', ''))
        f = open(file_path, 'wb')
        for chunk in myfiles[0].chunks():
            f.write(chunk)
        f.close()
        ch_obj = FbaTransportTask.objects.filter(file_path=file_path)
        obj = FbaTransportTask()
        if ch_obj:
            obj.id = ch_obj[0].id
            obj.created = datetime.datetime.now()
        else:
            obj.id
        obj.user = user.user
        obj.status = 'Uploaded'
        obj.file_path = file_path
        obj.save()
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully!'}), content_type='application/json')

@csrf_exempt
def run_fba_trans(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        ids = request.POST.getlist('ids', '')
        obj = FbaTransportTask.objects.filter(id__in=eval(ids[0]))
        work_path = settings.STOCHS_SPIDER_URL
        os.chdir(work_path)
        msg = 'Running~\n'
        for val in obj:
            xlsx_file = val.file_path.split('/')[-1]
            if not os.path.isfile(val.file_path):
                msg += '文件%s不存在\n' % xlsx_file
                continue
            os.popen('scrapyd-deploy')
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=fatl1_spider -d xlsx_file=%s' % xlsx_file
            os.popen(cmd_str)
        os.chdir(settings.ROOT_PATH)
        obj.update(status='Processing')
        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

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