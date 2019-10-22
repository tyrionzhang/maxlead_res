# -*- coding: utf-8 -*-
import json,os
import datetime,csv,codecs
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import StoreInfo
from maxlead import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def store_info(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    ordder_field = request.GET.get('ordder_field', 'created')
    order_desc = request.GET.get('order_desc', '-')
    data = []
    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit
    total_count = 0
    total_page = 0

    if user.user.is_superuser or user.group.user.username == 'Landy' or user.group.user.username == 'admin' or user.user.username == 'Landy':
        data = StoreInfo.objects.all()
        if ordder_field:
            order_by_str = "%s%s" % (order_desc, ordder_field)
            data = data.order_by(order_by_str)
        if data:
            for val in data:
                val.created = val.created.strftime('%Y-%m-%d %H:%M:%S')

            total_count = len(data)
            total_page = round(len(data) / int(limit))
            if int(limit) >= total_count:
                limit = total_count
            if data:
                paginator = Paginator(data, limit)
                try:
                    data = paginator.page(page)
                except PageNotAnInteger:
                    # If page is not an integer, deliver first page.
                    data = paginator.page(1)
                except EmptyPage:
                    # If page is out of range (e.g. 9999), deliver last page of results.
                    data = paginator.page(paginator.num_pages)
    data = {
        'data': data,
        'total_count': total_count,
        'total_page': total_page,
        're_limit': int(re_limit),
        'limit': int(limit),
        'page': page,
        'user': user,
        'ordder_field': ordder_field,
        'order_desc': order_desc,
        'avator': user.user.username[0],
    }
    return render(request, 'fba_acodtask/store_info.html', data)

@csrf_exempt
def store_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    res = []
    if request.method == 'POST':
        myfile = request.FILES.get('my_file','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        if myfile.name[-3:] != 'csv':
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File type error!'}), content_type='application/json')

        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        file = open(file_path, 'r', encoding='gb2312')
        csv_files = csv.reader(file)
        msg = 'Successfully!\n'
        for i, val in enumerate(csv_files, 0):
            if i == 0 and (not val[0] == 'Store ID' or not val[1] == 'Subsidiary' or val[2] != 'Payment' or
                           val[3] != 'Location' or val[4] != 'User' or val[5] != 'Time'):
                return HttpResponse(json.dumps({'code': 0, 'msg': u'文件错误~'}), content_type='application/json')
            try:
               if i > 0:
                   store_check = StoreInfo.objects.filter(store_id= val[0], subsidiary = val[1])
                   if store_check:
                       store_check.update(payment=val[2], location=val[3], user=user.user, created=datetime.datetime.now())
                   else:
                       obj = StoreInfo()
                       obj.id
                       obj.user = user.user
                       obj.store_id = val[0]
                       obj.subsidiary = val[1]
                       obj.payment = val[2]
                       obj.location = val[3]
                       obj.save()
            except:
                msg += '第%s行添加有误。\n' % (i + 1)
                continue
        file.close()
        res = {'code': 1, 'msg': msg}
        os.remove(file_path)
    return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def save_store(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        id = request.POST.get('id','')
        payment = request.POST.get('payment','')
        location = request.POST.get('location','')
        store_obj = StoreInfo.objects.filter(id=id)
        if not store_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在！'}), content_type='application/json')
        store_obj.update(payment=payment,location=location)
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}), content_type='application/json')

@csrf_exempt
def get_store(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'GET':
        store_id = request.GET.get('store_id','')
        store_list = StoreInfo.objects.filter(store_id__contains=store_id).order_by('store_id', '-id')
        store_data = []
        for val in store_list:
            store_data.append(val.store_id)
        return HttpResponse(json.dumps({'code': 1, 'data': store_data}), content_type='application/json')

