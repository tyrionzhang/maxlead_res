# -*- coding: utf-8 -*-
import os,json
from django.shortcuts import render,HttpResponse
from datetime import *
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import SkuUsers,StockLogs
from maxlead_site.common.excel_world import read_excel_file1
from maxlead import settings

@csrf_exempt
def sku_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    res = SkuUsers.objects.all()
    if keywords:
        res = res.filter(Q(sku__contains=keywords) | Q(user__username__contains=keywords))
    user_list = User.objects.all()
    if not user.user.is_superuser and not user.stocks_role == '66':
        res = res.filter(user_id=user.user.id)
        user_list = user_list.filter(id=user.user_id)
    limit = request.GET.get('limit', 50)
    page = request.GET.get('page', 1)
    re_limit = limit
    total_count = len(res)
    total_page = round(len(res) / int(limit))
    if int(limit) >= total_count:
        limit = total_count
    if res:
        paginator = Paginator(res, limit)
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
            'title': "User Skus",
            'keywords': keywords,
            'type': type,
            'user': user,
            'user_list': user_list
        }
    else:
        data = {
            'data': '',
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'title': "User Skus",
            'keywords': keywords,
            'type': type,
            'user': user,
            'user_list': user_list
        }
    return render(request, "Stocks/users_sku/skus.html", data)

@csrf_exempt
def save_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        user_id = request.POST.get('user_id', '')
        sku = request.POST.get('sku', '').replace('amp;','')
        if not user_id or not sku:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'user/sku is empty！'}), content_type='application/json')
        user_obj = User.objects.filter(id=user_id)
        if not user_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'user error！'}), content_type='application/json')
        check = SkuUsers.objects.filter(user_id=user_id,sku=sku)
        if not check:
            sku_users_obj = SkuUsers()
            sku_users_obj.id
            sku_users_obj.user_id = user_id
            sku_users_obj.sku = sku
            sku_users_obj.save()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')

@csrf_exempt
def import_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        myfile = request.FILES.get('myfile', '')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}), content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_file1(SkuUsers, file_path, 'sku_users')
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def del_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        sku_obj = SkuUsers.objects.filter(id=id)
        if not sku_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not found.'}), content_type='application/json')
        res = sku_obj.delete()
        if res:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}), content_type='application/json')

@csrf_exempt
def logs(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if not start_date:
        start_date = (datetime.now() + timedelta(days = -5)).strftime("%Y-%m-%d")
    res = StockLogs.objects.filter(created__gte=start_date).order_by('-created')
    if keywords:
        res = res.filter(Q(fun__contains=keywords)|Q(user__username__contains=keywords)|Q(description__contains=keywords))
    if start_date:
        res = res.filter(created__gte=start_date)
    if end_date:
        res = res.filter(created__lte=end_date)
    data = {
        'data': res,
        'keywords': keywords,
        'end_date': end_date,
        'start_date': start_date,
        'title': "Logs",
        'user': user,
    }
    return render(request, "Stocks/users_sku/logs.html", data)

@csrf_exempt
def del_user_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        ids = request.POST.getlist('ids', '')
        obj = SkuUsers.objects.filter(id__in=eval(ids[0]))
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not exist！'}), content_type='application/json')
        obj.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')