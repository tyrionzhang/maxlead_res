# -*- coding: utf-8 -*-
import json
import datetime
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from max_stock.models import KitSkuRes,KitSkus
from max_stock.views.views import search_kits,search_inv_sku,api_save_kit_sku
from max_stock.views.views import get_kit_skus

@csrf_exempt
def add_kit_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords','')
    type = request.GET.get('type', '')
    res = KitSkuRes.objects.all().order_by('-id', '-created')
    if not user.user.is_superuser:
        res = res.filter(user=user.user)
    if keywords:
        if type == 'kit':
            res = res.filter(kit__icontains=keywords)
        else:
            res = res.filter(sku__icontains=keywords)

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
            'title': "Add KitSKU",
            'keywords': keywords,
            'type': type,
            'user': user
        }
    else:
        data = {
            'data': '',
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'title': "Add KitSKU",
            'keywords': keywords,
            'type': type,
            'user': user
        }
    return render(request, "Stocks/add_kit_sku/add_kit_sku.html", data)

@csrf_exempt
def check_kit_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data', '')
        for i,val in enumerate(eval(data), 0):
            if not val['kit'] or not val['sku']:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Kit/SKU is empty！'}),
                                    content_type='application/json')
            if i == 0:
                check_str = ' */.\\'
                for v in check_str:
                    if v in val['kit']:
                        return HttpResponse(json.dumps({'code': 0, 'msg': u'您的输入包含特殊字符~'}),
                                            content_type='application/json')
                kit_re = search_kits(val['kit'])
                if kit_re == 11111:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Api Error！'}),
                                        content_type='application/json')
                if kit_re:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'KitSKU is exist！'}),
                                        content_type='application/json')
                sku_re = search_inv_sku(val['sku'])
                if sku_re == 11111:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Api Error！'}),
                                        content_type='application/json')
                if not sku_re['department'] or not sku_re['sales_person']:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Inventory SKU Error,SKU:%s is not exist!'}),
                                        content_type='application/json')
            else:
                sku_check = search_inv_sku(val['sku'])
                if sku_check == 11111:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Api Error！'}),
                                        content_type='application/json')
                if not sku_check['department'] or not sku_check['sales_person']:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Inventory SKU Error, SKU:%s is not exist!' % val['sku']}),
                                        content_type='application/json')
        return HttpResponse(json.dumps({'code': 1, 'data': sku_re}), content_type='application/json')

@csrf_exempt
def save_kit_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data', '')
        sku1 = request.POST.get('sku1', '')
        qty1 = request.POST.get('qty1', '')
        kit = request.POST.get('kit', '')
        stockdescription = request.POST.get('stockdescription', '')
        department = request.POST.get('department', '')
        sales_person = request.POST.get('sales_person', '')
        kit_country = request.POST.get('kit_country', '')
        res = {
            'kit': kit,
            'sku1': sku1,
            'qty1': qty1,
            'stockdescription': stockdescription,
            'department': department,
            'sales_person': sales_person,
            'lines': eval(data)
        }
        skus = []
        sku_pages = []
        sku_dict = {}
        for val in eval(data):
            page = val['sku'].split('-')[-1][0]
            sku_dict[page] = val['sku']
            sku_pages.append(page)
            skus.append(val['sku'])
        if len(skus) > 1:
            res['custitem35'] = sku_dict[min(sku_pages)]
        else:
            res['custitem35'] = skus[0]
        re = api_save_kit_sku(res, kit_country)
        skus = ','.join(skus)
        if re['code'] == 1001:
            return HttpResponse(json.dumps({'code': 0, 'msg': re['msg']}), content_type='application/json')
        obj = KitSkuRes()
        obj.id
        obj.kit = kit
        obj.sku = skus
        obj.user = user.user
        obj.save()
        kits = KitSkus.objects.all().order_by('-id', '-created')
        start_date = kits[0].created.strftime('%m/%d/%Y')
        get_kit_skus(start_date)
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Successfully!ID:%s' % re['id']}), content_type='application/json')