# -*- coding: utf-8 -*-
import os,json
import datetime
import requests
import threading
from urllib.parse import quote,unquote
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from max_stock.models import Barcodes
from maxlead import settings
from max_stock.views.views import get_barcodes,get_3pl_token

@csrf_exempt
def barcode(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    res = Barcodes.objects.all().order_by('status', '-id', '-created')
    if not res:
        sync_date = '11/01/2019 10:15'
    else:
        sync_date = res[0].created.strftime('%m/%d/%Y %H:%M:%S')

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
            'sync_date': sync_date,
            'title': "Barcode",
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
            'sync_date': sync_date,
            'title': "Barcode",
            'user': user
        }
    return render(request, "Stocks/barcode/barcode.html", data)

@csrf_exempt
def sync_barcode(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        start_date = request.POST.get('start_date', '')
        start_date = start_date[0:10]
        start_date = '11/01/2019 10:15'
        t = threading.Timer(3.0, run_update_barcode, [user, start_date])
        t.start()
    return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')

def run_update_barcode(user, start_date=None):
    barcs = get_barcodes(user.user, start_date)
    token_str = get_3pl_token()
    if barcs and token_str:
        headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept': "application/hal+json",
            'Host': "secure-wms.com",
            'Accept-Language': "en-US,en;q=0.8",
            'Accept-Encoding': "gzip,deflate,sdch",
            'Authorization': 'Bearer %s' % token_str
        }
        res = []
        for val in barcs:
            try:
                print(datetime.datetime.now(), 'Work is running~')
                if val['customer'] == 'MaxLead International Limited':
                    customer = 3
                else:
                    customer = 7
                url_itemid = 'https://secure-wms.com/customers/%s/items?rql=Sku==%s'
                url_put = 'https://secure-wms.com/customers/%s/items/%s'
                url_itemid = url_itemid % (customer, val['sku'])
                item = requests.get(url_itemid, headers=headers)
                if item.status_code != 200:
                    url_itemid = 'https://secure-wms.com/customers/%s/items?rql=Sku==*%s'
                    sku_r = quote(val['sku'], 'utf-8').replace('%', '%25')
                    url_itemid = url_itemid % (customer, sku_r)
                    item = requests.get(url_itemid, headers=headers)

                if item.status_code != 200:
                    res.append({
                        'sku': val['sku'],
                        'status': 'N'
                    })
                    continue
                else:
                    item = json.loads(item.content.decode())
                    if item['totalResults'] == 0:
                        res.append({
                            'sku': val['sku'],
                            'status': 'Invalid'
                        })
                        continue
                item_id = item['_embedded']['http://api.3plCentral.com/rels/customers/item'][0]['itemId']
                url_put = url_put % (customer, item_id)
                headers.update({'Content-Type': 'application/hal+json; charset=utf-8'})
                et_res = requests.get(url_put, headers=headers)
                headers.update({'If-Match': et_res.headers['Etag']})
                params = json.loads(et_res.content.decode())
                params.update({"upc": val['barcode']})
                params['options']["pallets"].update({"upc": val['barcode']})
                params['options']["packageUnit"].update({"upc": val['barcode']})
                response = requests.put(url_put, json=params, headers=headers)
                if response.status_code == 200:
                    res.append({
                        'sku': val['sku'],
                        'status': 'Y'
                    })
                    continue
                else:
                    res.append({
                        'sku': val['sku'],
                        'status': 'N'
                    })
                    continue
            except Exception as e :
                res.append({
                    'sku': val['sku'],
                    'status': 'N'
                })
                print(datetime.datetime.now(), 'SKU:%s |' % val['sku'], e)
                continue
        if res:
            y_li = []
            n_li = []
            i_li = []
            for val in res:
                if val['status'] == 'Y':
                    y_li.append(val['sku'])
                elif val['status'] == 'N':
                    n_li.append(val['sku'])
                else:
                    i_li.append(val['sku'])
            if y_li:
                Barcodes.objects.filter(sku__in=y_li).update(user=user.user, status='Y')
            if n_li:
                Barcodes.objects.filter(sku__in=n_li).update(user=user.user, status='N')
            if i_li:
                Barcodes.objects.filter(sku__in=i_li).update(user=user.user, status='Invalid')