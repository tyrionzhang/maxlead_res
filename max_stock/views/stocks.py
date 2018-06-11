# -*- coding: utf-8 -*-
import os,json
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from maxlead_site.common.excel_world import read_excel_file1,read_excel_data,get_excel_file
from maxlead_site.views.app import App
from maxlead import settings
from max_stock.views import views
from django.db.models import Count
from django.core.mail import send_mail

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords','').replace('amp;','')
    warehouse = request.GET.get('warehouse','')
    sel_new = request.GET.get('sel_new','')
    stocks = WarehouseStocks.objects.all()
    if not user.user.is_superuser:
        skus = SkuUsers.objects.filter(user_id=user.user.id).values_list('sku')
        stocks = stocks.filter(sku__in=skus)
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if warehouse:
        stocks = stocks.filter(warehouse=warehouse)
    if sel_new:
        stocks = stocks.filter(is_new=sel_new)
    stocks = stocks.values('sku','warehouse').annotate(count=Count('sku'),count2=Count('warehouse'))
    items = []
    qty_old = 0
    have_new = 0
    for key,val in enumerate(stocks,0):
        old = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'],is_new=0)
        new = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'],is_new=1)
        re = {
            'sku':val['sku'],
            'warehouse':val['warehouse'],
            'is_same':0,
            'is_new_type':0,
            'qty_new':0,
            'qty_old':0,
            'created':'',
        }
        if new:
            re.update({'qty_new':new[0].qty,'created':new[0].created.strftime("%Y-%m-%d %H:%M:%S")})
            re.update({'is_new_type': 1})
            have_new = 1
        if old:
            qty_old = old[0].qty
            re.update({'qty_old':qty_old,'created':old[0].created.strftime("%Y-%m-%d %H:%M:%S")})

        threshold_obj = Thresholds.objects.filter(sku=val['sku'], warehouse=val['warehouse'])
        if threshold_obj and threshold_obj[0].threshold >= qty_old:
            re.update({'is_same':1})
        items.append(re)

    data = {
        'stock_list':items,
        'user': user,
        'keywords': keywords,
        'warehouse': warehouse,
        'sel_new': sel_new,
        'have_new': have_new,
        'title': 'Inventory',
    }
    return render(request,"Stocks/stocks/index.html",data)

@csrf_exempt
def stock_checked(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    data = []
    if request.method == 'POST':
        myfile = request.FILES.get('myfile','')
        type = request.POST.get('type','')
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
                is_same = ''
                if re:
                    if not re[0].qty == val['qty']:
                        is_same = 1
                    id = re[0].id
                    qty_old = re[0].qty
                else:
                    id = 0
                    qty_old = 0
                    is_same = 1
                re1.update({
                    'id':id,
                    'sku':val['sku'],
                    'warehouse':val['warehouse'],
                    'qty_old':qty_old,
                    'qty_new':val['qty'],
                    'is_same':is_same,
                })
                if type == 'new':
                    re1.update({'type':type})
                data.append(re1)
            os.remove(file_path)
        data = {
            'data':data,
            'user': user,
            'title': 'Inventory-Check',
            'type': type,
        }
    return render(request, "Stocks/stocks/stock_checked.html", data)

@csrf_exempt
def checked_edit(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = int(request.POST.get('id',''))
        qty = request.POST.get('qty','')
        sku = request.POST.get('sku','').replace('amp;','')
        warehouse = request.POST.get('warehouse','')
        type = request.POST.get('type','')
        if id:
            res = WarehouseStocks.objects.filter(id=id)
            if not res:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not found!'}), content_type='application/json')
        if type == 'new':
            if id:
                i = res.update(qty=qty)
            else:
                obj = WarehouseStocks()
                obj.id
                obj.sku = sku
                obj.warehouse = warehouse
                obj.qty = qty
                obj.is_new = 0
                obj.save()
                i = obj.id
            if i:
                data = {
                    'user': user.user,
                    'fun': request.path,
                    'description': 'Sku:%s,QTY covered by %s.' % (sku, qty),
                }
            re_qty = qty
        else:
            qtys = res[0].qty-int(qty)
            i = res.update(qty=qtys)
            if i:
                data = {
                    'user':user.user,
                    'fun':request.path,
                    'description':'Sku:%s,QTY lower %s.' % (res[0].sku,qty),
                }
            re_qty = qtys
        views.save_logs(data)
        return HttpResponse(json.dumps({'code': 1, 'data': re_qty}), content_type='application/json')

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
                        qtys = re[0].qty - val['qty_new']
                        i = re.update(qty=qtys)
                        if i:
                            data = {
                                'user': user.user,
                                'fun': request.path,
                                'description': 'Sku:%s,QTY lower %s.' % (re[0].sku, val['qty_new']),
                            }
                            views.save_logs(data)
                except:
                    msg += "第%s行修改有误！\n" % i
                    continue

        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def export_stocks(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    warehouse = request.GET.get('warehouse', '')
    sel_new = request.GET.get('sel_new', '')
    stocks = WarehouseStocks.objects.all()
    if not user.user.is_superuser:
        skus = SkuUsers.objects.filter(user_id=user.user.id).values_list('sku')
        stocks = stocks.filter(sku__in=skus)
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if warehouse:
        stocks = stocks.filter(warehouse=warehouse)
    if not sel_new:
        sel_new = 0
    stocks = stocks.filter(is_new=sel_new)
    stocks = stocks.values('sku', 'warehouse').annotate(count=Count('sku'), count2=Count('warehouse'))

    data = []
    if stocks:
        for val in stocks:
            qty = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'],is_new=sel_new)
            if qty:
                re = {
                    'sku':val['sku'],
                    'warehouse':val['warehouse'],
                    'qty':qty[0].qty,
                    'created':qty[0].created.strftime("%Y-%m-%d %H:%M:%S"),
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
    sku = request.GET.get('keywords','').replace('amp;','')
    warehouse = request.GET.get('warehouse','')
    list = Thresholds.objects.all()
    if sku:
        list = list.filter(sku__contains=sku)
    if not user.user.is_superuser:
        skus = SkuUsers.objects.filter(user_id=user.user.id).values_list('sku')
        list = list.filter(sku__in=skus)
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
        sku = request.POST.get('sku','').replace('amp;','')
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

@csrf_exempt
def check_new(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data','')
        if data:
            data = eval(data)
            for val in data:
                try:
                    obj = WarehouseStocks.objects.filter(sku=val['sku'].replace('amp;',''),warehouse=val['warehouse'],is_new=1)
                    if obj:
                        obj.delete()
                except:
                    continue
                return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfuly!'}),content_type='application/json')

@csrf_exempt
def check_all_new(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data','')
        if data:
            data = eval(data)
            querylist = []
            msgs = []
            subject = 'Maxlead库存预警'
            from_email = settings.EMAIL_HOST_USER
            for val in data:
                val['sku'] = val['sku'].replace('amp;','')
                try:
                    obj = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'],is_new=0)
                    if obj:
                        i = obj.update(qty=val['qty'])
                    else:
                        querylist.append(WarehouseStocks(sku=val['sku'],warehouse=val['warehouse'],qty=val['qty'],is_new=0))
                    threshold = Thresholds.objects.filter(sku=val['sku'], warehouse=val['warehouse'])
                    user = SkuUsers.objects.filter(sku=val['sku'])
                    if threshold and threshold[0].threshold >= int(val['qty']):
                        if user:
                            msg = 'SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n' % (val['sku'], val['warehouse'], val['qty'], threshold[0].threshold)
                            msgs.append({'email':user[0].user.email,'msg':msg})
                    data_log = {
                        'user': user.user,
                        'fun': request.path,
                        'description': 'Sku:%s,QTY covered by %s.' % (val['sku'], val['qty']),
                    }
                    views.save_logs(data_log)
                except:
                    continue

            if querylist:
                WarehouseStocks.objects.bulk_create(querylist)
            # 发送提示邮件
            if msgs:
                dict_msg = {}
                all_msg = ''
                for i,val in enumerate(msgs,0):
                    msg_res_str = val['msg']
                    for n,v in enumerate(msgs,0):
                        if not i == n and v['email'] == val['email']:
                            msg_res_str += v['msg']
                    dict_msg.update({val['email']: msg_res_str})
                for key in dict_msg:
                    all_msg += dict_msg[key]
                    send_mail(subject, dict_msg[key], from_email, [key], fail_silently=False)
                send_mail(subject, all_msg, from_email, ['shipping.gmi@gmail.com'], fail_silently=False)

            return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfuly!'}),content_type='application/json')

def covered_stocks(user,data,path):
    create_obj = WarehouseStocks()
    create_obj.id
    create_obj.sku = data['sku'].replace('amp;','')
    create_obj.warehouse = data['warehouse']
    create_obj.created = data['date']
    create_obj.qty = data['qty_new']
    create_obj.is_new = 0
    create_obj.save()
    if not create_obj.id:
        return {'code':0,'msg':'Failed!'}
    data_log = {
        'user': user,
        'fun': path,
        'description': 'Sku:%s,QTY covered by %s.' % (create_obj.sku, data['qty_new']),
    }
    views.save_logs(data_log)
    obj = WarehouseStocks.objects.filter(sku=create_obj.sku, warehouse=data['warehouse']).exclude(id=create_obj.id).delete()
    if obj:
        return {'code':1,'msg':'Successfully!'}

@csrf_exempt
def covered_new(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        sku = request.POST.get('sku','').replace('amp;','')
        warehouse = request.POST.get('warehouse','')
        qty_new = request.POST.get('qty_new','')
        date = request.POST.get('date','')
        res = covered_stocks(user.user,{'sku':sku,'warehouse':warehouse,'qty_new':qty_new,'date':date},request.path)
        return HttpResponse(json.dumps({'code': res['code'], 'msg': res['msg']}), content_type='application/json')

@csrf_exempt
def covered_new_all(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data','')
        if data:
            data = eval(data)
            for val in data:
                try:
                    covered_stocks(user.user,val,request.path)
                except:
                    continue
            return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully!'}), content_type='application/json')

@csrf_exempt
def covered_give_up(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        data = request.POST.get('data','')
        if data:
            data = eval(data)
            for val in data:
                try:
                    val['sku'] = val['sku'].replace('amp;','')
                    obj = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'],is_new=1)
                    if obj:
                        obj.delete()
                except:
                    continue
            return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully!'}), content_type='application/json')