# -*- coding: utf-8 -*-
import os,json
import xlrd
import time
import threading
import itertools
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import KitSkus,Sfps,Thresholds,WarehouseStocks,SfpTemps
from django.http import StreamingHttpResponse
from maxlead import settings

@csrf_exempt
def sfp_items(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;','')
    res = Sfps.objects.filter(user_id=user.user.id)
    if keywords:
        res = res.filter(item__contains=keywords)

    kits = KitSkus.objects.all().order_by('-id', '-created')
    kit_date = kits[0].created.strftime('%m/%d/%Y %H:%M:%S')
    if res:
        sku_list = []
        data_re = []
        kits_re = {}
        for val in kits:
            kits_re.update({
                val.kit: val.sku
            })
        for val in res:
            if val.item in kits_re:
                kits = KitSkus.objects.filter(kit=val.item)
                for k_val in kits:
                    data_re.append({
                        'id': val.id,
                        'kit': val.item,
                        'sku': k_val.sku
                    })
                    sku_list.append(k_val.sku)
            else:
                data_re.append({
                    'id': val.id,
                    'kit': '',
                    'sku': val.item
                })
                sku_list.append(val.item)
        th_re = Thresholds.objects.filter(sku__in=sku_list)
        date_re = WarehouseStocks.objects.filter(sku__in=sku_list).order_by('-created')[0]

        ware_re = WarehouseStocks.objects.filter(sku__in=sku_list,created__contains=date_re.created.strftime('%Y-%m-%d'))
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
            sku_key = val.sku + val.warehouse
            if sku_key not in th_li or th_li[sku_key] < 10:
                chec_th = 10
            else:
                chec_th = th_li[sku_key]
            if val.qty >= chec_th:
                if val.sku in sku_ware:
                    if val.warehouse not in sku_ware[val.sku]:
                        sku_ware[val.sku] = sku_ware[val.sku] + val.warehouse + ','
                else:
                    sku_ware.update({
                        val.sku : val.warehouse + ','
                    })
        sfps_re = {}
        sfps = SfpTemps.objects.all().exclude(inactive='Y')
        for val in sfps:
            if 'TWU' in val.warehouse or 'EXL' in val.warehouse:
                w_list = val.warehouse.split(',')
                w_list.append('TX')
                if 'TWU' in w_list:
                    w_list.remove('TWU')
                if 'EXL' in w_list:
                    w_list.remove('EXL')
                val.warehouse = ','.join(w_list)
            sfps_re.update({
                val.warehouse : val.sfp_temp
            })
        res = {}
        for val in data_re:
            if val['sku'] in sku_ware:
                wares = sku_ware[val['sku']][0:-1]
                val.update({'whs': wares})
                if wares == 'EXL' or wares == 'TWU':
                    val.update({'sfp': 'Prime template--TX ONLY'})
                else:
                    if 'TWU' in wares or 'EXL' in wares:
                        w_list = wares.split(',')
                        w_list.append('TX')
                        if 'TWU' in w_list:
                            w_list.remove('TWU')
                        if 'EXL' in w_list:
                            w_list.remove('EXL')
                        wares = ','.join(w_list)
                    wares_re = itertools.permutations(wares.split(','))
                    sfp_t = ''
                    for w_val in wares_re:
                        check_w = ','.join(w_val)
                        if check_w in sfps_re:
                            sfp_t = sfps_re[check_w]
                            break
                    if sfp_t:
                        val.update({'sfp': sfp_t})
                    else:
                        val.update({'sfp': 'Default Amazon Template'})
            else:
                val.update({
                    'whs': '',
                    'sfp': 'Default Amazon Template'
                })

            if not val['kit']:
                val['kit'] = 'kit'+ val['sku']
                is_kit = 0
            else:
                is_kit = 1
            if val['kit'] not in res:
                res.update({
                    val['kit'] : {
                        'id' : val['id'],
                        'sku' : val['sku'],
                        'is_kit' : is_kit,
                        'whs' : val['whs'],
                        'sfp' : val['sfp']
                    }
                })
            else:
                sku_str = res[val['kit']]['sku'] + ','+ val['sku']
                if len(val['whs']) < len(res[val['kit']]['whs']):
                    whs = val['whs']
                    sfp = val['sfp']
                else:
                    whs = res[val['kit']]['whs']
                    sfp = res[val['kit']]['sfp']
                res[val['kit']].update({
                    'sku': sku_str,
                    'is_kit': is_kit,
                    'whs': whs,
                    'sfp': sfp
                })

    data = {
        'data': res,
        'kit_date': kit_date,
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
                    chec = Sfps.objects.filter(item=item, user=user.user)
                    if chec:
                        msg += '第%s行已存在。<br>' % (i + 1)
                    else:
                        querylist.append(Sfps(item=item, user=user.user))
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
    res = Sfps.objects.filter(user_id=user.user.id)
    if keywords:
        res = res.filter(item__contains=keywords)
    if not res:
        return HttpResponseRedirect("/admin/max_stock/sfp/")
    data_re = []
    sku_list = []
    kits_re = {}
    kits = KitSkus.objects.all()
    for val in kits:
        kits_re.update({
            val.kit : val.sku
        })
    for val in res:
        if val.item in kits_re:
            kits = KitSkus.objects.filter(kit=val.item)
            for k_val in kits:
                data_re.append({
                    'kit': val.item,
                    'sku': k_val.sku
                })
                sku_list.append(k_val.sku)
        else:
            data_re.append({
                'kit': '',
                'sku': val.item
            })
            sku_list.append(val.item)
    th_re = Thresholds.objects.filter(sku__in=sku_list)
    date_re = WarehouseStocks.objects.filter(sku__in=sku_list).order_by('-created')[0]
    ware_re = WarehouseStocks.objects.filter(sku__in=sku_list, created__contains=date_re.created.strftime('%Y-%m-%d'))
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
        sku_key = val.sku + val.warehouse
        if sku_key not in th_li or th_li[sku_key] < 10:
            chec_th = 10
        else:
            chec_th = th_li[sku_key]
        if val.qty >= chec_th:
            if val.sku in sku_ware:
                sku_ware[val.sku] = sku_ware[val.sku] + val.warehouse + ','
            else:
                sku_ware.update({
                    val.sku: val.warehouse + ','
                })
    sfps_re = {}
    sfps = SfpTemps.objects.all().exclude(inactive='Y')
    for val in sfps:
        if 'TWU' in val.warehouse or 'EXL' in val.warehouse:
            w_list = val.warehouse.split(',')
            w_list.append('TX')
            if 'TWU' in w_list:
                w_list.remove('TWU')
            if 'EXL' in w_list:
                w_list.remove('EXL')
            val.warehouse = ','.join(w_list)
        sfps_re.update({
            val.warehouse: val.sfp_temp
        })
    res = {}
    for val in data_re:
        if val['sku'] in sku_ware:
            wares = sku_ware[val['sku']][0:-1]
            val.update({'whs': wares})
            if wares == 'EXL' or wares == 'TWU':
                val.update({'sfp': 'Prime template--TX ONLY'})
            else:
                if 'TWU' in wares or 'EXL' in wares:
                    w_list = wares.split(',')
                    w_list.append('TX')
                    if 'TWU' in w_list:
                        w_list.remove('TWU')
                    if 'EXL' in w_list:
                        w_list.remove('EXL')
                    wares = ','.join(w_list)
                wares_re = itertools.permutations(wares.split(','))
                sfp_t = ''
                for w_val in wares_re:
                    check_w = ','.join(w_val)
                    if check_w in sfps_re:
                        sfp_t = sfps_re[check_w]
                        break
                if sfp_t:
                    val.update({'sfp': sfp_t})
                else:
                    val.update({'sfp': 'Default Amazon Template'})
        else:
            val.update({
                'whs': '',
                'sfp': 'Default Amazon Template'
            })

        if not val['kit']:
            val['kit'] = 'kit' + val['sku']
            is_kit = 0
        else:
            is_kit = 1
        if val['kit'] not in res:
            res.update({
                val['kit']: {
                    'sku': val['sku'],
                    'is_kit': is_kit,
                    'whs': val['whs'],
                    'sfp': val['sfp']
                }
            })
        else:
            sku_str = res[val['kit']]['sku'] + ',' + val['sku']
            if len(val['whs']) < len(res[val['kit']]['whs']):
                whs = val['whs']
                sfp = val['sfp']
            else:
                whs = res[val['kit']]['whs']
                sfp = res[val['kit']]['sfp']
            res[val['kit']].update({
                'sku': sku_str,
                'is_kit': is_kit,
                'whs': whs,
                'sfp': sfp
            })

    contents = ''
    for key, val in res.items():
        if val['is_kit']:
            sku = key
        else:
            sku = val['sku']
        contents += '%s	%s\n' % (sku, val['sfp'])
    if contents:
        file_name = 'SFP-%s.txt' % (time.strftime('%Y-%m-%d-%H%M%S'))
        with open(file_name, 'w') as f:
            f.write('sku	merchant_shipping_group_name\n')
            f.write(contents)
            f.close()
        def file_iterator(file_name):
            with open(file_name) as f:
                while True:
                    c = f.read()
                    if c:
                        yield c
                    else:
                        break
                f.close()
        response = StreamingHttpResponse(file_iterator(file_name))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)
        t = threading.Timer(300.0, remove_file,[file_name])
        t.start()
        return response

@csrf_exempt
def save_sfp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        item = request.POST.get('item', '')
        check = Sfps.objects.filter(item=item, user=user.user)
        if check:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is exists！'}), content_type='application/json')
        sfp_obj = Sfps()
        sfp_obj.id
        sfp_obj.user = user.user
        sfp_obj.item = item
        sfp_obj.save()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')

def remove_file(path):
    os.remove(path)

@csrf_exempt
def del_items(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        ids = request.POST.getlist('ids', '')
        obj = Sfps.objects.filter(id__in=eval(ids[0]))
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not exist！'}), content_type='application/json')
        obj.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')