# -*- coding: utf-8 -*-
import os,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import WarehouseStocks,Thresholds
from maxlead_site.common.excel_world import read_excel_file1,read_excel_data,get_excel_file
from maxlead_site.views.app import App
from maxlead import settings

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
        'keywords': keywords,
        'warehouse': warehouse,
        'title': 'Inventory',
    }
    return render(request,"Stocks/stocks/index.html",data)

@csrf_exempt
def stock_checked(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    data = []
    cover_data = ''
    if request.method == 'POST':
        myfile = request.FILES.get('myfile','')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_data(WarehouseStocks, file_path)
        if res:
            for val in res:
                re1 = {}
                re = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'])
                if re:
                    is_same = ''
                    if not re[0].qty == val['qty']:
                        is_same = 1
                    re1.update({
                        'id':re[0].id,
                        'sku':val['sku'],
                        'warehouse':val['warehouse'],
                        'qty_old':re[0].qty,
                        'qty_new':val['qty'],
                        'is_same':is_same,
                    })
                    data.append(re1)
            os.remove(file_path)
    data = {
        'data':data,
        'user': user,
        'title': 'Inventory-Check',
    }
    return render(request, "Stocks/stocks/stock_checked.html", data)

@csrf_exempt
def checked_edit(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        qty = request.POST.get('qty','')
        res = WarehouseStocks.objects.filter(id=id)
        if not res:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not found!'}), content_type='application/json')
        i = res.update(qty=qty)
        if i:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Work is done!'}), content_type='application/json')

@csrf_exempt
def checked_batch_edit(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data_stock','')
        msg = '操作成功！\n'
        if data:
            data = eval(data)
            for i,val in enumerate(data,1):
                try:
                    re = WarehouseStocks.objects.filter(id=val['id'])
                    if re:
                        re.update(qty=val['qty_new'])
                except:
                    msg += "第%s行修改有误！\n" % i
                    continue

        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def export_stocks(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '')
    warehouse = request.GET.get('warehouse', '')
    stocks = WarehouseStocks.objects.all()
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if warehouse:
        stocks = stocks.filter(warehouse=warehouse)

    data = []
    if stocks:
        for val in stocks:
            re = {
                'sku':val.sku,
                'warehouse':val.warehouse,
                'qty':val.qty,
                'created':val.created.strftime("%Y-%m-%d %H:%M:%S"),
            }
            data.append(re)
        fields = ['SKU','Warehouse','QTY','Created']
        data_fields = ['sku','warehouse','qty','created']
        return get_excel_file(request, data, fields, data_fields)
    else:
        return HttpResponse('没有数据~~')

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
        'keywords':sku,
        'warehouse':warehouse,
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

@csrf_exempt
def threshold_del(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        if id:
            res = Thresholds.objects.filter(id=id).delete()
            if res:
                return HttpResponse(json.dumps({'code': 1, 'data': 0}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Is faild!'}),
                                    content_type='application/json')
        else:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Error,data is not found!'}),
                                content_type='application/json')

@csrf_exempt
def threshold_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        myfile = request.FILES.get('myfile','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_file1(Thresholds,file_path,'stock_thresholds')
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')