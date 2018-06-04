# -*- coding: utf-8 -*-
import os,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
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
    if not user.user.is_superuser:
        skus = SkuUsers.objects.filter(user_id=user.user.id).values_list('sku')
        if skus:
            res = res.filter(sku__in=skus)
    if keywords:
        res = res.filter(Q(sku__contains=keywords) | Q(user__username__contains=keywords))
    user_list = User.objects.filter(userprofile__role=99)
    data = {
        'data': res,
        'title': "UserAdmin",
        'user': user,
        'user_list': user_list,
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
    res = StockLogs.objects.all()
    if keywords:
        res = res.filter(Q(fun__contains=keywords)|Q(user__username__contains=keywords)|Q(description__contains=keywords))
    data = {
        'data': res,
        'title': "Logs",
        'user': user,
    }
    return render(request, "Stocks/users_sku/logs.html", data)