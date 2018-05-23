# -*- coding: utf-8 -*-
import time,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import WarehouseStocks,Thresholds
from django.db.models import Q
from maxlead_site.views import commons
from maxlead_site.views.app import App

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords','')
    warehouse = request.GET.get('warehouse','')
    stocks = WarehouseStocks.objects.all()
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if warehouse:
        stocks = stocks.filter(warehouse=warehouse)
    for val in stocks:
        val.created = val.created.strftime("%Y-%m-%d %H:%M:%S")

    data = {
        'stock_list':stocks,
        'user': user,
        'title': 'Inventory',
    }
    return render(request,"Stocks/stocks/index.html",data)

# threshold start
@csrf_exempt
def threshold(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    sku = request.GET.get('keywords','')
    warehouse = request.GET.get('warehouse','')
    list = Thresholds.objects.all()
    if sku:
        list = list.filter(sku__contains=sku)
    if warehouse:
        list = list.filter(warehouse__contains=warehouse)
    # for val in list:
    #     val.created = val.created.strftime("%Y-%m-%d %H:%M:%S")
    data = {
        'user':user,
        'list':list,
        'title':'Setting',
    }
    return render(request,"Stocks/stocks/threshold.html",data)

@csrf_exempt
def threshold_add(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        sku = request.POST.get('sku','')
        warehouse = request.POST.get('warehouse','')
        threshold = request.POST.get('threshold',0)
        id = request.POST.get('id',0)
        if not sku or not warehouse:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'sku/warehouse is empty！'}), content_type='application/json')
        else:
            if id:
                checked = Thresholds.objects.filter(sku=sku, warehouse=warehouse).exclude(id=id)
                if checked:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Was existed!'}),
                                        content_type='application/json')
                else:
                    res = Thresholds.objects.filter(id=id).update(sku=sku,warehouse=warehouse,threshold=threshold)
                    if res:
                        return HttpResponse(json.dumps({'code': 1, 'msg': u'This edit has been completed!'}),
                                            content_type='application/json')
            else:
                checked = Thresholds.objects.filter(sku=sku, warehouse=warehouse)
                if checked:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Was existed!'}),
                                        content_type='application/json')
                else:
                    threshold_obj = Thresholds()
                    threshold_obj.id
                    threshold_obj.sku = sku
                    threshold_obj.warehouse = warehouse
                    threshold_obj.threshold = threshold
                    threshold_obj.save()
                    if threshold_obj.id:
                        return HttpResponse(json.dumps({'code': 1, 'msg': u'This add has been completed!'}),
                                            content_type='application/json')
                    else:
                        return HttpResponse(json.dumps({'code': 0, 'msg': u'Is faild!'}),
                                        content_type='application/json')
@csrf_exempt
def get_threshold(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        if id:
            res = Thresholds.objects.get(id=id)
            data = {
                'sku':res.sku,
                'warehouse':res.warehouse,
                'threshold':res.threshold,
            }
            return HttpResponse(json.dumps({'code': 1, 'data': data}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Error,data is not found!'}), content_type='application/json')