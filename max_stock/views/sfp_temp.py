# -*- coding: utf-8 -*-
import os,json
import xlrd
from django.shortcuts import render,HttpResponse
from datetime import *
from django.http import HttpResponseRedirect
from django.db.models import Q
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import SfpTemps,KitSkus
from maxlead_site.common.excel_world import get_excel_file
from maxlead import settings
from max_stock.views.views import get_kit_skus

@csrf_exempt
def sfp_temp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    res = SfpTemps.objects.all()
    if keywords:
        res = res.filter(Q(sfp_temp__contains=keywords) | Q(warehouse__contains=keywords))
    data = {
        'data': res,
        'title': "Sfp Temp",
        'user': user
    }
    return render(request, "Stocks/sfp/sfp_temp.html", data)

@csrf_exempt
def save_stemp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        sfp_temp = request.POST.get('sfp_temp', '')
        warehouse = request.POST.get('warehouse', '')
        id = request.POST.get('id', '')
        inactive = request.POST.get('inactive', '')
        check = SfpTemps.objects.filter(sfp_temp=sfp_temp)
        if id:
            if inactive == 'Y':
                SfpTemps.objects.filter(id=id).update(inactive='Y')
                return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')
            check = check.exclude(id=id)
        if check:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is exists！'}), content_type='application/json')
        if not check:
            sku_users_obj = SfpTemps()
            sku_users_obj.id
            if id:
                sku_users_obj.id = id
            sku_users_obj.sfp_temp = sfp_temp
            sku_users_obj.warehouse = warehouse
            sku_users_obj.user = user.user
            sku_users_obj.created = datetime.now()
            sku_users_obj.save()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')

@csrf_exempt
def import_stemp(request):
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
        check_data = []
        for i in range(nrows):
            try:
                if i + 1 < nrows:
                    sfp_temp = table.cell_value(i + 1, 0, ).strip()
                    warehouse = table.cell_value(i + 1, 1, ).strip()
                    inactive = table.cell_value(i + 1, 2, ).strip()
                    chec = SfpTemps.objects.filter(sfp_temp=sfp_temp)
                    if chec:
                        chec.update(warehouse=warehouse, inactive=inactive, user=user.user)
                    else:
                        if sfp_temp not in check_data:
                            check_data.append(sfp_temp)
                            querylist.append(SfpTemps(sfp_temp=sfp_temp, warehouse=warehouse, inactive=inactive, user=user.user))
            except:
                msg += '第%s行添加有误。<br>' % (i + 1)
            continue
        if querylist:
            SfpTemps.objects.bulk_create(querylist)
        os.remove(file_path)
        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def export_stemp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    keywords = request.GET.get('keywords', '')
    res = SfpTemps.objects.all()
    if keywords:
        res = res.filter(Q(sfp_temp__contains=keywords) | Q(warehouse__contains=keywords))

    data = []
    for val in res:
        re = {
            'sfp_temp':val.sfp_temp,
            'warehouse':val.warehouse,
            'inactive':val.inactive,
            'user':val.user.username,
            'created':val.created.strftime("%Y-%m-%d %H:%M:%S")
        }
        data.append(re)

    fields = [
        'SFP Template',
        'Warehouse',
        'Inactive',
        'User',
        'Date'
    ]

    data_fields = [
        'sfp_temp',
        'warehouse',
        'inactive',
        'user',
        'created'
    ]

    return get_excel_file(request, data, fields, data_fields)

@csrf_exempt
def import_kit(request):
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
        edit_list = []
        for i in range(nrows):
            try:
                if i + 1 < nrows:
                    kit = table.cell_value(i + 1, 0, )
                    sku = table.cell_value(i + 1, 1, )
                    key = kit + sku
                    chec = KitSkus.objects.filter(key=key)
                    if chec:
                        chec.update(sku=sku, kit=kit)
                    else:
                        if key not in edit_list:
                            edit_list.append(key)
                            querylist.append(KitSkus(kit=kit, sku=sku, key=key))
            except:
                msg += '第%s行添加有误。<br>' % (i + 1)
            continue
        if querylist:
            KitSkus.objects.bulk_create(querylist)
        os.remove(file_path)
        return HttpResponse(json.dumps({'code': 1, 'msg': msg}), content_type='application/json')

@csrf_exempt
def update_kits(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        start_date = request.POST.get('start_date', '')
        start_date = start_date[0:10]
        # kits = KitSkus.objects.all().delete()
        get_kit_skus(start_date)
    return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')