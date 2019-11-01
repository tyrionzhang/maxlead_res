# -*- coding: utf-8 -*-
import os,json
import xlrd
from django.shortcuts import render,HttpResponse
from datetime import *
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db.models import Q
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import KitSkus,Sfps,Thresholds,WarehouseStocks,SfpTemps
from maxlead_site.common.excel_world import get_excel_file
from maxlead import settings

@csrf_exempt
def sfp_items(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    res = Sfps.objects.all()
    if keywords:
        res = res.filter(item__contains=keywords)
    data_re = []
    sku_list = []
    for val in res:
        kit_chec = KitSkus.objects.filter(kit=val.item)
        if kit_chec:
            data_re.append({
                'kit' : val.item,
                'sku' : kit_chec[0].sku
            })
            sku_list.append(kit_chec[0].sku)
        else:
            kit_chec = KitSkus.objects.filter(sku=val.item)
            if kit_chec:
                data_re.append({
                    'kit': '',
                    'sku': kit_chec[0].sku
                })
                sku_list.append(kit_chec[0].sku)
    th_re = Thresholds.objects.filter(sku__in=sku_list)
    date_re = WarehouseStocks.objects.filter(sku__in=sku_list).order_by('-created')
    ware_re = WarehouseStocks.objects.filter(sku__in=sku_list,created__contains=date_re[0].created.strftime('%Y-%m-%d'))
    th_li = {}
    sku_ware = {}
    for val in th_re:
        if val.warehouse == 'Hanover':
            val.warehouse = 'HW'
        th_li.update({
            val.sku+val.warehouse : val.threshold
        })
    for val in ware_re:
        if val.warehouse == 'Hanover':
            val.warehouse = 'HW'
        if val.sku not in th_li or th_li[val.sku+val.warehouse] < 30:
            chec_th = 30
        else:
            chec_th = th_li[val.sku + val.warehouse]
        if val.qty >= chec_th:
            if val.sku in sku_ware:
                sku_ware[val.sku] = sku_ware[val.sku] + val.warehouse + ','
            else:
                sku_ware.update({
                    val.sku : val.warehouse + ','
                })
    for val in data_re:
        if val['sku'] in sku_ware:
            wares = sku_ware[val['sku']][0:-1]
            sfp_t = SfpTemps.objects.filter(warehouse=wares).exclude(inactive='Y')
            if sfp_t:
                val.update({'sfp': sfp_t[0].sfp_temp})
            else:
                val.update({'sfp': ''})
            val.update({'whs' : wares})
        else:
            val.update({
                'whs': '',
                'sfp': ''
            })

    data = {
        'data': data_re,
        'title': "Sfp Items",
        'user': user
    }
    return render(request, "Stocks/sfp/sfp_items.html", data)

@csrf_exempt
def import_sitem(request):
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
        if not os.path.isfile(file_path):
            return HttpResponse(json.dumps({'code': 0, 'msg': 'File is not found!'}), content_type='application/json')
        data = xlrd.open_workbook(file_path)  # 打开fname文件
        data.sheet_names()  # 获取xls文件中所有sheet的名称
        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
        nrows = table.nrows
        msg = ''
        querylist = []
        for i in range(nrows):
            try:
                if i + 1 < nrows:
                    item = table.cell_value(i + 1, 0, )
                    chec = Sfps.objects.filter(item=item)
                    if chec:
                        msg += '第%s行已存在。<br>' % (i + 1)
                    else:
                        querylist.append(Sfps(item=item))
            except:
                msg += '第%s行添加有误。<br>' % (i + 1)
            continue
        if querylist:
            Sfps.objects.bulk_create(querylist)
        os.remove(file_path)
        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def export_sfp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    keywords = request.GET.get('keywords', '').replace('amp;', '')
    res = Sfps.objects.all()
    if keywords:
        res = res.filter(item__contains=keywords)
    data_re = []
    sku_list = []
    for val in res:
        kit_chec = KitSkus.objects.filter(kit=val.item)
        if kit_chec:
            data_re.append({
                'kit': val.item,
                'sku': kit_chec[0].sku
            })
            sku_list.append(kit_chec[0].sku)
        else:
            kit_chec = KitSkus.objects.filter(sku=val.item)
            if kit_chec:
                data_re.append({
                    'kit': '',
                    'sku': kit_chec[0].sku
                })
                sku_list.append(kit_chec[0].sku)
    th_re = Thresholds.objects.filter(sku__in=sku_list)
    date_re = WarehouseStocks.objects.filter(sku__in=sku_list).order_by('-created')
    ware_re = WarehouseStocks.objects.filter(sku__in=sku_list, created__contains=date_re[0].created.strftime('%Y-%m-%d'))
    th_li = {}
    sku_ware = {}
    for val in th_re:
        if val.warehouse == 'Hanover':
            val.warehouse = 'HW'
        th_li.update({
            val.sku + val.warehouse: val.threshold
        })
    for val in ware_re:
        if val.warehouse == 'Hanover':
            val.warehouse = 'HW'
        if val.sku not in th_li or th_li[val.sku + val.warehouse] < 30:
            chec_th = 30
        else:
            chec_th = th_li[val.sku + val.warehouse]
        if val.qty >= chec_th:
            if val.sku in sku_ware:
                sku_ware[val.sku] = sku_ware[val.sku] + val.warehouse + ','
            else:
                sku_ware.update({
                    val.sku: val.warehouse + ','
                })
    for val in data_re:
        if val['sku'] in sku_ware:
            wares = sku_ware[val['sku']][0:-1]
            sfp_t = SfpTemps.objects.filter(warehouse=wares).exclude(inactive='Y')
            if sfp_t:
                val.update({'sfp': sfp_t[0].sfp_temp})
            else:
                val.update({'sfp': ''})
            val.update({'whs': wares})
        else:
            val.update({
                'whs': '',
                'sfp': ''
            })
    fields = [
        'Kit',
        'SKU',
        'WHS',
        'SFP',
    ]

    data_fields = [
        'kit',
        'sku',
        'whs',
        'sfp'
    ]

    return get_excel_file(request, data_re, fields, data_fields)

@csrf_exempt
def save_sfp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        item = request.POST.get('item', '')
        check = Sfps.objects.filter(item=item)
        if check:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is exists！'}), content_type='application/json')
        sfp_obj = Sfps()
        sfp_obj.id
        sfp_obj.item = item
        sfp_obj.save()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')