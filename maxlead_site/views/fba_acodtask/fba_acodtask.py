# -*- coding: utf-8 -*-
import json,os
import datetime,threading
import zipfile
import time
import csv
from chardet.universaldetector import UniversalDetector
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from io import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import FbaAccountingTask,StoreInfo
from maxlead import settings
from django.views.decorators.csrf import csrf_exempt

def check_chart(path):
    detector = UniversalDetector()
    detector.reset()
    for each in open(path, 'rb'):
        detector.feed(each)
        if detector.done:
            break
    detector.close()
    fileencoding = detector.result['encoding']
    return fileencoding

def del_file(file_path, id):
    if os.path.isfile(file_path):
        os.remove(file_path)
        obj = FbaAccountingTask.objects.filter(id=id)
        if obj:
            obj.update(path='')
@csrf_exempt
def fba_acodtask(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    ordder_field = request.GET.get('ordder_field', 'created')
    order_desc = request.GET.get('order_desc', '-')
    data = []
    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit
    total_count = 0
    total_page = 0
    if int(page) <= 0:
        page = 1

    store_data = []
    if user.user.is_superuser or user.group.user.username == 'Landy' or user.group.user.username == 'admin' or user.user.username == 'Landy':
        store_list = StoreInfo.objects.all().order_by('store_id', '-id')
        for val in store_list:
            store_data.append(val.store_id)
        data = FbaAccountingTask.objects.all()
        if ordder_field:
            order_by_str = "%s%s" % (order_desc, ordder_field)
            data = data.order_by(order_by_str)
        if data:
            for val in data:
                val.created = val.created.strftime('%Y-%m-%d %H:%M:%S')
                val.date_range = '%s/%s' % (val.date_range, val.date_range_end)

            total_count = len(data)
            total_page = round(len(data) / int(limit))
            if int(limit) >= total_count:
                limit = total_count
            if data:
                paginator = Paginator(data, limit)
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
        'user': user,
        'ordder_field': ordder_field,
        'order_desc': order_desc,
        'date_range': datetime.datetime.now().strftime('%Y-%m-%d'),
        'avator': user.user.username[0],
        'store_list': store_data
    }
    return render(request, 'fba_acodtask/fba_acodtask.html', data)

@csrf_exempt
def fba_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    res = []
    if request.method == 'POST':
        myfile = request.FILES.get('my_file','')
        store_id = request.POST.get('store_id','')
        date_range = request.POST.get('date_range','')
        date_range_end = request.POST.get('date_range_end','')
        date_range_str = time.mktime(time.strptime(date_range,'%Y-%m-%d'))
        date_range_end_str = time.mktime(time.strptime(date_range_end,'%Y-%m-%d'))
        store_info = StoreInfo.objects.filter(store_id=store_id)
        if not store_info:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Store Id error!'}), content_type='application/json')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        if myfile.name[-3:] != 'txt':
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File type error!'}), content_type='application/json')

        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        char_str = check_chart(file_path)
        file = open(file_path, 'r', encoding=char_str)
        line = file.readline()
        msg = 'Successfully!\n'
        file_name1 = 'Fba-Account-customer%s.csv' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        file_name2 = 'Fba-Account-order%s.csv' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        file_name3 = 'Fba-Account-bill%s.csv' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        file_name4 = 'Fba-Account-tracking%s.csv' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        files_dir1 = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, file_name1)
        files_dir2 = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, file_name2)
        files_dir3 = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, file_name3)
        files_dir4 = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, file_name4)
        customer_title = ['Individual', 'Subsidiary', 'First Name', 'Last Name', 'Sales Rep', 'Category', 'Email',
                          'Mobile Phone', 'Attention', 'Addressee', 'Shipping Phone', 'Address Line1', 'Address Line2',
                          'City', 'State', 'Zipcode', 'Country', 'Default Shipping', 'Currency']
        order_title = ['Externalid','PO#', 'Date', 'Customer', 'Status', 'Memo', 'StoreID', 'Subsidiary', 'Walmart Order#',
                       'Currency', 'Payment Method', 'SKU', 'Location', 'Quantity', 'Rate', 'Amount', 'TaxCode',
                       'Item Tax', 'Shipping Fee', 'Selling Fees', 'FBA Fees', 'Other Fees', 'Sort']
        bill_title = ['PO#']
        tracking_title = ['PO#', 'ShipDate', 'Memo', 'Status', 'Carrier', 'Method', 'SKU', 'Tracking', 'Weight']
        i = 0
        check_li = {}
        customer_row = []
        order_row = []
        bill_row = []
        tracking_row = []
        while line:
            line = file.readline()
            if line:
                try:
                    val = line.split('\t')
                    if val[0][0:1] == 'S':
                        continue
                    i += 1
                    buyer_name = val[11]
                    b_name = buyer_name.find(' ')
                    if b_name == -1:
                        first_name = buyer_name
                        last_name = 'ML'
                    else:
                        first_name = buyer_name[:b_name]
                        last_name = buyer_name[b_name+1:]
                    if val[8]:
                        shp_date_re = val[8][:10].split('-')
                        shp_date = '%s/%s/%s' % (shp_date_re[1], shp_date_re[2], shp_date_re[0])
                        shp_date1 = shp_date_re[1] + shp_date_re[2]
                        shp_date_str = time.mktime(time.strptime(shp_date, '%m/%d/%Y'))
                        if float(shp_date_str) < float(date_range_str) or float(shp_date_str) > float(date_range_end_str):
                            continue
                    else:
                        continue
                    if not val[17]:
                        val[17] = 0
                    if not val[40]:
                        val[40] = 0
                    amount = float(val[17]) + float(val[40])
                    rate = 0
                    if val[15]:
                        rate = amount/float(val[15])
                    amount = '%.2f' % amount
                    rate = '%.2f' % rate
                    if store_info[0].subsidiary == 'MaxLead International Limited : Match Land International limited':
                        carrier = val[42] + '-1'
                    else:
                        carrier = val[42]
                    po_sku = val[0]
                    if po_sku in check_li:
                        check_li.update({
                            po_sku : check_li[po_sku] + 1
                        })
                    else:
                        check_li.update({
                            po_sku : 0
                        })
                    sort = check_li[po_sku]
                    customer_row.append(['T',store_info[0].subsidiary,first_name,last_name,'','B2C Customer',val[10],val[12],
                                    '', val[24],'',val[25],'',val[28],val[29],val[30],'United States','T',val[16]])
                    order_row.append(['%s#%s#%s' % (shp_date1,val[0],store_id),val[0],shp_date,val[24],
                                 'Pending Fulfillment','',store_id,store_info[0].subsidiary,'',val[16],store_info[0].payment,
                                 val[13],store_info[0].location,val[15],rate,amount,'',0,0,0,0,0,sort])
                    bill_row.append(['%s#%s#%s' % (shp_date1,val[0],store_id)])
                    tracking_row.append(['%s#%s#%s' % (shp_date1,val[0],store_id),shp_date,'','C',carrier,carrier,val[13],'',1])
                except:
                    msg += '第%s行添加有误。\n' % (i + 1)
                    continue

        if customer_row:
            with open(files_dir1, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                # 先写入columns_name
                writer.writerow(customer_title)
                # 写入多行用writerows
                writer.writerows(customer_row)
            csvfile.close()

            with open(files_dir2, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                # 先写入columns_name
                writer.writerow(order_title)
                # 写入多行用writerows
                writer.writerows(order_row)
            csvfile.close()

            with open(files_dir3, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                # 先写入columns_name
                writer.writerow(bill_title)
                # 写入多行用writerows
                writer.writerows(bill_row)
            csvfile.close()

            with open(files_dir4, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                # 先写入columns_name
                writer.writerow(tracking_title)
                # 写入多行用writerows
                writer.writerows(tracking_row)
            csvfile.close()
        else:
            file.close()
            return HttpResponse(json.dumps({'code': 1, 'msg': '没有符合条件的数据.'}), content_type='application/json')

        file.close()
        res = {'code': 1, 'msg': msg}
        zip_name = 'Fba-Account-export%s.zip' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        zip_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, zip_name)
        f = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        f.write(files_dir1, file_name1)
        f.write(files_dir2, file_name2)
        f.write(files_dir3, file_name3)
        f.write(files_dir4, file_name4)
        f.close()
        os.remove(files_dir1)
        os.remove(files_dir2)
        os.remove(files_dir3)
        os.remove(files_dir4)
        f_path_re = zip_path.split('download')
        f_path = '/download%s' % f_path_re[1]
        obj = FbaAccountingTask()
        obj.id
        obj.user = user.user
        obj.store_id = store_info[0]
        obj.date_range = date_range
        obj.date_range_end = date_range_end
        obj.path = f_path
        obj.save()
        t = threading.Timer(1800, del_file, [zip_path,obj.id])
        t.start()
    return HttpResponse(json.dumps(res), content_type='application/json')