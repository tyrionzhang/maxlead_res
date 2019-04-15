# -*- coding: utf-8 -*-
import os,json
from datetime import *
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import WarehouseStocks,Thresholds,SkuUsers
from maxlead_site.models import Employee
from maxlead_site.common.excel_world import read_excel_file1,read_excel_data,get_excel_file
from maxlead_site.views.app import App
from maxlead import settings
from max_stock.views import views
from django.db.models import Count
from django.core.mail import send_mail

warehouse= {
    'exl' : 'EXL',
    'twu' : 'TWU',
    'ego' : 'EGO',
    'tfd' : 'TFD',
    'hanover' : 'Hanover',
    'atl' : 'ATL-1',
    'pc' : 'PC'
}
@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords','').replace('amp;','')
    warehouse = request.GET.get('warehouse','')
    sel_new = request.GET.get('sel_new','')
    start_date = request.GET.get('start_date','')
    end_date = request.GET.get('end_date','')
    if not warehouse:
        warehouse = 'TWU'
    if not start_date:
        start_date = datetime.now()
        start_date = start_date.strftime('%Y-%m-%d')
    stocks_url = '/admin/max_stock/get_stocks?%s'
    get_str = ''
    url_data = request.get_raw_uri().split('?')
    if len(url_data) > 1:
        get_str = url_data[1]
    stocks_url = stocks_url % get_str

    data = {
        'user': user,
        'keywords': keywords,
        'warehouse': warehouse,
        'sel_new': sel_new,
        'start_date': start_date,
        'end_date': end_date,
        'stocks_url': stocks_url,
        'menu_id': user.menu_parent_id,
        'title': 'Inventory',
    }
    return render(request,"Stocks/stocks/index.html",data)

@csrf_exempt
def get_stocks(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;', '')
    warehouse = request.GET.get('warehouse', '')
    sel_new = request.GET.get('sel_new', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if not start_date:
        start_date = datetime.now()
        start_date = start_date.strftime('%Y-%m-%d')
    stocks = WarehouseStocks.objects.filter(created__gte=start_date).order_by('sku', '-qty')
    if not user.user.is_superuser and not user.stocks_role == '66':
        uids = [user.user_id]
        if user.stocks_role == '88':
            child_user = Employee.objects.filter(parent_user=user.user_id)
            if child_user:
                for val in child_user:
                    uids.append(val.user_id)
        skus = SkuUsers.objects.filter(user_id__in=uids).values_list('sku')
        skus_li = []
        if skus:
            for val in skus:
                skus_li.append(val[0].strip())
        stocks = stocks.filter(sku__in=skus_li)

    if end_date:
        stocks = stocks.filter(created__lte=end_date)
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if not warehouse:
        warehouse = 'TWU'
    if not warehouse == 'all':
        stocks = stocks.filter(warehouse=warehouse)
    if sel_new:
        stocks = stocks.filter(is_new=sel_new)
    select_data = {"d": """date_trunc('day', created)"""}
    stocks = stocks.extra(select=select_data).values('sku', 'd').annotate(count=Count('sku'))
    items = []
    have_new = 0
    d_list = []
    for value in stocks:
        del value['count']
        if not d_list or value not in d_list:
            d_list.append(value)

    for key, val in enumerate(d_list, 0):
        re = {
            'sku': val['sku'],
            'exl': {'qty': 0, 'is_same': 0},
            'twu': {'qty': 0, 'is_same': 0},
            'ego': {'qty': 0, 'is_same': 0},
            'tfd': {'qty': 0, 'is_same': 0},
            'hanover': {'qty': 0, 'is_same': 0},
            'atl': {'qty': 0, 'is_same': 0},
            'pc': {'qty': 0, 'is_same': 0}
        }
        obj = WarehouseStocks.objects.filter(sku=val['sku'], created__contains=val['d'].strftime('%Y-%m-%d'))
        sum = 0
        for v in obj:
            if v.warehouse == 'EXL':
                re['exl'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['exl'].update({'is_same': 1})
            elif v.warehouse == 'TWU':
                re['twu'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['twu'].update({'is_same': 1})
            elif v.warehouse == 'EGO':
                re['ego'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['ego'].update({'is_same': 1})
            elif v.warehouse == 'TFD':
                re['tfd'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['tfd'].update({'is_same': 1})
            elif v.warehouse == 'Hanover':
                re['hanover'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['hanover'].update({'is_same': 1})
            elif v.warehouse == 'PC':
                re['pc'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['pc'].update({'is_same': 1})
            else:
                re['atl'].update({'qty': v.qty})
                sum += int(v.qty)
                threshold_obj = Thresholds.objects.filter(sku=v.sku, warehouse=v.warehouse)
                if threshold_obj and threshold_obj[0].threshold >= v.qty:
                    re['atl'].update({'is_same': 1})
            date_re = v.created.strftime('%Y-%m-%d %H:%M:%S')
        re.update({'sum': sum, 'date': date_re})
        items.append(re)
    data = {
        'stock_list': items,
        'user': user,
        'have_new': have_new,
    }
    return render(request, "Stocks/stocks/stocks_list.html", data)

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
        edit_type = ''
        if res:
            for i, val in enumerate(res, 1):
                re1 = {}
                re = WarehouseStocks.objects.filter(sku=val['sku'],warehouse=val['warehouse'])
                date_str = datetime.now().strftime("%Y-%m-%d")
                if re:
                    try:
                        re = re.filter(created__contains=val['created'][:10])
                        date_str = val['created'][:10]
                    except:
                        re = re.filter(created__contains=date_str)
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
                if qty_old < val['qty']:
                    edit_type += '有OOS:第%s行,sku:%s\\n' % (i, val['sku'])
                re1.update({
                    'id':id,
                    'sku':val['sku'],
                    'warehouse':val['warehouse'],
                    'qty_old':qty_old,
                    'qty_new':val['qty'],
                    'is_same':is_same,
                    'date':date_str,
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
            'edit_type': edit_type,
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
        date_str = request.POST.get('date_str','')
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
                check = WarehouseStocks.objects.filter(sku=sku, warehouse=warehouse, created__contains=datetime.now().strftime('%Y-%m-%d'))
                if check:
                    check.delete()
                obj = WarehouseStocks()
                obj.id
                obj.sku = sku
                obj.warehouse = warehouse
                obj.qty = qty
                obj.created = date_str
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
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if not start_date:
        start_date = datetime.now()
        start_date = start_date.strftime('%Y-%m-%d')
    stocks = WarehouseStocks.objects.filter(created__gte=start_date).order_by('sku', '-qty')
    if not user.user.is_superuser and not user.stocks_role == '66':
        skus = SkuUsers.objects.filter(user_id=user.user.id).values_list('sku')
        skus_li = []
        if skus:
            for val in skus:
                skus_li.append(val[0].strip())
        stocks = stocks.filter(sku__in=skus_li)
    if end_date:
        stocks = stocks.filter(created__lte=end_date)
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if not warehouse:
        warehouse = 'EXL'
    if not warehouse == 'all':
        stocks = stocks.filter(warehouse=warehouse)
    select_data = {"d": """date_trunc('day', created)"""}
    stocks = stocks.extra(select=select_data).values('sku', 'd').annotate(count=Count('sku'))
    data = []
    d_list = []
    for value in stocks:
        del value['count']
        if not d_list or not value in d_list:
            d_list.append(value)

    for key, val in enumerate(d_list, 0):
        re = {
            'sku': val['sku'],
            'exl': '0',
            'twu': '0',
            'ego': '0',
            'tfd': '0',
            'hanover': '0',
            'atl': '0',
            'pc': '0'
        }
        obj = WarehouseStocks.objects.filter(sku=val['sku'], created__contains=val['d'].strftime('%Y-%m-%d'))
        sum = 0
        for v in obj:
            if v.warehouse == 'EXL':
                re.update({'exl': v.qty})
                sum += int(v.qty)
            elif v.warehouse == 'TWU':
                re.update({'twu': v.qty})
                sum += int(v.qty)
            elif v.warehouse == 'EGO':
                re.update({'ego': v.qty})
                sum += int(v.qty)
            elif v.warehouse == 'TFD':
                re.update({'tfd': v.qty})
                sum += int(v.qty)
            elif v.warehouse == 'Hanover':
                re.update({'hanover': v.qty})
                sum += int(v.qty)
            elif v.warehouse == 'PC':
                re.update({'pc': v.qty})
                sum += int(v.qty)
            else:
                re.update({'atl': v.qty})
                sum += int(v.qty)
            date_re = v.created.strftime('%Y-%m-%d %H:%M:%S')
        re.update({'sum': sum, 'date': date_re})
        data.append(re)
    if data:
        fields = ['SKU','EXL','TWU','EGO','TFD','Hanover','ATL','SUM','Created']
        data_fields = ['sku','exl','twu','ego','tfd','hanover','atl','sum','date']
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
    if not user.user.is_superuser and not user.stocks_role == '66':
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
    create_obj.qty = data['qty_new']
    create_obj.qty1 = data['qty1']
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
    obj = WarehouseStocks.objects.filter(sku=create_obj.sku, warehouse=data['warehouse'], is_new=1).delete()
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
        res = covered_stocks(user.user,{'sku':sku,'warehouse':warehouse,'qty_new':qty_new},request.path)
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

@csrf_exempt
def sales_vol(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;', '')
    warehouse = request.GET.get('warehouse', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if not start_date:
        start_date = datetime.now()
        start_date = start_date.strftime('%Y-%m-%d')
    stocks = WarehouseStocks.objects.filter(created__gte=start_date).order_by('qty1', 'sku' )
    if not user.user.is_superuser and not user.stocks_role == '66':
        uids = [user.user_id]
        if user.stocks_role == '88':
            child_user = Employee.objects.filter(parent_user=user.user_id)
            if child_user:
                for val in child_user:
                    uids.append(val.user_id)
        skus = SkuUsers.objects.filter(user_id__in=uids).values_list('sku')
        skus_li = []
        if skus:
            for val in skus:
                skus_li.append(val[0].strip())
        stocks = stocks.filter(sku__in=skus_li)
    if end_date:
        stocks = stocks.filter(created__lte=end_date)
    if keywords:
        stocks = stocks.filter(sku__contains=keywords)
    if not warehouse:
        warehouse = 'TWU'
    if not warehouse == 'all':
        stocks = stocks.filter(warehouse=warehouse)
    select_data = {"d": """date_trunc('day', created)"""}
    stocks = stocks.extra(select=select_data).values('sku', 'd').annotate(count=Count('sku'))
    items = []
    d_list = []
    sales_date = []
    for value in stocks:
        del value['count']
        if not d_list or not value in d_list:
            d_list.append(value)

    for key, val in enumerate(d_list, 0):
        re = {
            'sku': val['sku'],
            'exl': 0,
            'twu': 0,
            'ego': 0,
            'tfd': 0,
            'hanover': 0,
            'atl': 0,
            'sum': 0
        }
        contain_date = val['d'].strftime('%Y-%m-%d')
        obj = WarehouseStocks.objects.filter(sku=val['sku'], created__contains=contain_date)
        sum = 0
        sakes_check = 0
        for v in obj:
            if v.warehouse == 'EXL':
                re['exl'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            elif v.warehouse == 'TWU':
                re['twu'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            elif v.warehouse == 'EGO':
                re['ego'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            elif v.warehouse == 'TFD':
                re['tfd'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            elif v.warehouse == 'Hanover':
                re['hanover'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            else:
                re['atl'] = v.qty1
                sum += int(v.qty1)
                if v.qty1 < 0:
                    sakes_check = 1
            date_re = v.created.strftime('%Y-%m-%d %H:%M:%S')
        re.update({'sum': sum, 'date': date_re})
        if sakes_check:
            re.update({'is_sales': 1})
        items.append(re)
        if sakes_check and contain_date not in sales_date:
            sales_date.append(contain_date)
    sales_msg = False
    if sales_date:
        str_date = ','.join(sales_date)
        sales_msg = u'%s有补货，请添加或上传补货信息。' % str_date
    data = {
        'stock_list': items,
        'user': user,
        'keywords': keywords,
        'warehouse': warehouse,
        'start_date': start_date,
        'end_date': end_date,
        'menu_id': user.menu_parent_id,
        'sales_msg': sales_msg,
        'title': 'Sales Data',
    }
    return render(request, "Stocks/stocks/sales_vol.html", data)

@csrf_exempt
def stock_sales(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    data = []
    if request.method == 'POST':
        myfile = request.FILES.get('myfile','')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_data(1, file_path)
        if res:
            for val in res:
                val['date'] = val['date'].strftime('%Y-%m-%d')
                re1 = {
                    'sku' : val['sku'],
                    'exl' : 0,
                    'twu' : 0,
                    'ego' : 0,
                    'tfd' : 0,
                    'hanover' : 0,
                    'atl' : 0,
                    'date' : val['date'],
                    'error' : ''
                }
                re = WarehouseStocks.objects.filter(sku=val['sku'],created__contains=val['date'], qty1__lt=0)
                if re:
                    for v in re:
                        qty1_str = u'%s补货%s'
                        if v.warehouse == 'EXL':
                            re1.update({'exl' : qty1_str % (v.qty1, val['exl'])})
                        elif v.warehouse == 'TWU':
                            re1.update({'twu' : qty1_str % (v.qty1, val['twu'])})
                        elif v.warehouse == 'EGO':
                            re1.update({'ego' : qty1_str % (v.qty1, val['ego'])})
                        elif v.warehouse == 'TFD':
                            re1.update({'tfd' : qty1_str % (v.qty1, val['tfd'])})
                        elif v.warehouse == 'Hanover':
                            re1.update({'hanover' : qty1_str % (v.qty1, val['hanover'])})
                        else:
                            re1.update({'atl': qty1_str % (v.qty1, val['atl'])})
                else:
                    re1.update({'error' : u'没有补货。'})
                data.append(re1)
            os.remove(file_path)
        data = {
            'list':data,
            'user': user,
            'title': 'Stock Sales',
        }
    return render(request, "Stocks/stocks/stock_sales.html", data)

@csrf_exempt
def save_sales(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data','')
        msg = '操作成功！\n'
        if data:
            data = eval(data)
            for i,val in enumerate(data,1):
                try:
                    if not val['exl'] == '0':
                        sales = val['exl'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='EXL', created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='EXL', created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                    if not val['twu'] == '0':
                        sales = val['twu'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='TWU',
                                                            created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='TWU',
                                                                  created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                    if not val['ego'] == '0':
                        sales = val['ego'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='EGO',
                                                            created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='EGO',
                                                                  created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                    if not val['tfd'] == '0':
                        sales = val['tfd'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='TFD',
                                                            created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='TFD',
                                                                  created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                    if not val['hanover'] == '0':
                        sales = val['hanover'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='Hanover',
                                                            created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='Hanover',
                                                                  created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                    if not val['atl'] == '0':
                        sales = val['atl'].split('补货')
                        date1 = datetime.strptime(val['date'], '%Y-%m-%d') - timedelta(days=1)
                        re = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='ATL-1',
                                                            created__contains=val['date'], qty1__lt=0)
                        if re:
                            obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse='ATL-1',
                                                                  created__contains=date1.strftime('%Y-%m-%d'))
                            obj1.update(qty=obj1[0].qty + int(sales[1]))
                            re.update(qty1=obj1[0].qty - re[0].qty)
                except:
                    msg += "第%s行修改有误！\n" % i
                    continue

        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def ajax_save_sales(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        data = request.POST.get('data','')
        if data:
            for val in eval(data):
                date1 = datetime.strptime(val['date'], '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
                obj = WarehouseStocks.objects.filter(sku=val['sku'], warehouse=warehouse[val['warehouse']], created__contains=val['date'][:10],
                                                     qty1__lt=0)
                if obj:
                    obj1 = WarehouseStocks.objects.filter(sku=val['sku'], warehouse=warehouse[val['warehouse']],
                                                         created__contains=date1.strftime('%Y-%m-%d'))
                    obj1.update(qty=obj1[0].qty + int(val['num']))
                    obj.update(qty1=obj1[0].qty - obj[0].qty)
    return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfuly!'}), content_type='application/json')


