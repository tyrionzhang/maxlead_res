# -*- coding: utf-8 -*-
import json,os
import datetime,csv,threading
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.utils import OperationalError
import xlsxwriter
from io import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import FbaAccountingTask,StoreInfo
from maxlead import settings
from django.views.decorators.csrf import csrf_exempt

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
        'date_range': datetime.datetime.now().strftime('%Y-%m'),
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
        store_info = StoreInfo.objects.filter(store_id=store_id)
        if not store_info:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Store Id error!'}), content_type='application/json')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        if myfile.name[-3:] != 'csv':
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File type error!'}), content_type='application/json')

        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        file = open(file_path, 'r', encoding='utf-8')
        csv_files = csv.reader(file)
        msg = 'Successfully!\n'
        file_name = 'Fba-Account-export%s.xlsx' % (datetime.datetime.now().strftime('%Y-%m-%d %H%M%S'))
        files_dir = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, file_name)
        workbook = xlsxwriter.Workbook(files_dir)
        customer_sheet = workbook.add_worksheet(u"Customer")
        order_sheet = workbook.add_worksheet(u"Order")
        bill_sheet = workbook.add_worksheet(u"Bill")
        tracking_sheet = workbook.add_worksheet(u"Tracking")
        bold = workbook.add_format({'bold': 1, 'align': 'center'})
        customer_title = ['Individual', 'Subsidiary', 'First Name', 'Last Name', 'Sales Rep', 'Category', 'Email',
                          'Mobile Phone', 'Attention', 'Addressee', 'Shipping Phone', 'Address Line1', 'Address Line2',
                          'City', 'State', 'Zipcode', 'Country', 'Default Shipping', 'Currency', 'Sort']
        order_title = ['Externalid','PO#', 'Date', 'Customer', 'Status', 'Memo', 'StoreID', 'Subsidiary', 'Walmart Order#',
                       'Currency', 'Payment Method', 'SKU', 'Location', 'Quantity', 'Rate', 'Amount', 'TaxCode',
                       'Item Tax', 'Shipping Fee', 'Selling Fees', 'FBA Fees', 'Other Fees', 'Sort']
        bill_title = ['PO#']
        tracking_title = ['PO#', 'ShipDate', 'Memo', 'Status', 'Carrier', 'Method', 'SKU', 'Tracking', 'Weight', 'Sort']
        customer_sheet.write_row('A1', customer_title, bold)
        order_sheet.write_row('A1', order_title, bold)
        bill_sheet.write_row('A1', bill_title, bold)
        tracking_sheet.write_row('A1', tracking_title, bold)
        for i, val in enumerate(csv_files, 0):
            try:
                if i > 0:
                    buyer_name = val[11]
                    b_name = buyer_name.find(' ')
                    if b_name == -1:
                        first_name = buyer_name
                        last_name = ''
                    else:
                        first_name = buyer_name[:b_name]
                        last_name = buyer_name[b_name+1:]
                    shp_date = ''
                    if val[8]:
                        shp_date_re = val[8][:10].split('-')
                        shp_date = '%s/%s/%s' % (shp_date_re[2], shp_date_re[1], shp_date_re[0])
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
                    customer_row = ['T',store_info[0].subsidiary,first_name,last_name,'','B2C Customer',val[10],val[12],
                                    '', val[24],'',val[25],'',val[28],val[29],val[30],'','',val[16],i]
                    order_row = ['%s&%s&%s' % (date_range[2:].replace('-',''),val[0],store_id),val[0],shp_date,val[24],
                                 'Pending Fulfillment','',store_id,store_info[0].subsidiary,'',val[16],store_info[0].payment,
                                 val[13],store_info[0].location,val[15],rate,amount,0,0,0,0,0,0,i]
                    bill_row = [val[0]]
                    tracking_row = [val[0],shp_date,'','C',carrier,carrier,val[13],val[43],1,i]
                    customer_sheet.write_row('A%s' % str(i+1), customer_row)
                    order_sheet.write_row('A%s' % str(i+1), order_row)
                    bill_sheet.write_row('A%s' % str(i+1), bill_row)
                    tracking_sheet.write_row('A%s' % str(i+1), tracking_row)
            except OperationalError:
                msg += '第%s行添加有误。\n' % (i + 1)
                continue
        res = {'code': 1, 'msg': msg}
        workbook.close()
        f_path_re = files_dir.split('download')
        f_path = '/download%s' % f_path_re[1]
        obj = FbaAccountingTask()
        obj.id
        obj.user = user.user
        obj.store_id = store_info[0]
        obj.date_range = date_range
        obj.path = f_path
        obj.save()
        t = threading.Timer(1800, del_file, [files_dir,obj.id])
        t.start()
    return HttpResponse(json.dumps(res), content_type='application/json')