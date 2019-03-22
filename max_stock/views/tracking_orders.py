# -*- coding: utf-8 -*-
import os,json,time
import datetime
import requests,threading
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import TrackingOrders,StockLogs
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from maxlead import settings
from maxlead_site.common.excel_world import read_excel_for_tracking_orders,get_excel_file1,get_excel_file

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    keywords = request.GET.get('keywords', '').replace('amp;', '')
    billing_date_search = request.GET.get('billing_date', '')
    if not billing_date_search:
        billing_date = datetime.datetime.now().strftime("%b.%y")
    else:
        billing_date = time.strptime(billing_date_search, "%Y-%m-%d")
        billing_date = time.strftime('%b.%y',time.localtime(time.mktime(billing_date)))
    if user.user.is_superuser or user.stocks_role == '66':
        lists = TrackingOrders.objects.all()
    else:
        lists = TrackingOrders.objects.filter(user_id=user.user_id)
    if keywords:
        lists = lists.filter(Q(order_num__contains=keywords)|Q(tracking_num__contains=keywords))
    if billing_date:
        lists = lists.filter(billing_date__contains=billing_date)
    data = []
    if lists:
        for val in lists:
            first_scan_time = ''
            delivery_time = ''
            if val.first_scan_time:
                first_scan_time = val.first_scan_time.strftime("%Y-%m-%d %H:%M:%S")
            if val.delivery_time:
                delivery_time = val.delivery_time.strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                'order_num': val.order_num,
                'tracking_num': val.tracking_num,
                'warehouse': val.warehouse,
                'account_num': val.account_num,
                'description': val.description,
                'status': val.status,
                'shipment_late': val.shipment_late,
                'delivery_late': val.delivery_late,
                'billing_date': val.billing_date,
                'latest_ship_date': val.latest_ship_date,
                'latest_delivery_date': val.latest_delivery_date,
                'first_scan_time': first_scan_time,
                'delivery_time': delivery_time
            })

    data = {
        'user': user,
        'data': data,
        'billing_date': billing_date,
        'keywords': keywords,
        'title': 'TrackingOrders',
    }
    return render(request, "Stocks/trackingOrders/index.html", data)

@csrf_exempt
def import_tracking(request):
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
        res = read_excel_for_tracking_orders(file_path, user=user.user_id)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

def get_tracking_order_status():
    # billing_date = datetime.datetime.now().strftime("%b.%y")
    # lists = TrackingOrders.objects.filter(billing_date__contains=billing_date)
    t = threading.Timer(86400.0, get_tracking_order_status)
    lists = TrackingOrders.objects.all()
    data = []
    for val in lists:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
        }
        url = 'http://shipit-api.herokuapp.com/api/carriers/%s/%s'
        if len(val.tracking_num) > 12:
            carrier = 'ups'
        else:
            carrier = 'fedex'
        url = url % (carrier, val.tracking_num)
        res = requests.get(url, headers=headers)
        # try:
        res = json.loads(res.content.decode())
        activities = res['activities']
        if activities:
            status = activities[0]['details']
            first_scan_time = ''
            delivery_time = ''
            shipment_late = ''
            delivery_late = ''
            for v in activities:
                if v['details'] == 'Picked up' and carrier == 'fedex':
                    first_scan_time = datetime.datetime.strptime(v['datetime'], '%Y-%m-%dT%H:%M:%S')
                    first_scan_time = first_scan_time + datetime.timedelta(hours=-7)
                if v['details'] == 'Delivered':
                    delivery_time = datetime.datetime.strptime(v['datetime'], '%Y-%m-%dT%H:%M:%S')
                    delivery_time = delivery_time + datetime.timedelta(hours=-7)
                if v['details'] == 'Origin scan' and carrier == 'ups':
                    first_scan_time = datetime.datetime.strptime(v['datetime'], '%Y-%m-%dT%H:%M:%S')
                    first_scan_time = first_scan_time + datetime.timedelta(hours=-7)
                if first_scan_time:
                    if val.latest_ship_date and len(val.latest_ship_date) >= 20:
                        first_scan_time_str = int(time.mktime(first_scan_time.timetuple()))
                        latest_ship_date_str = int(
                            time.mktime(time.strptime(val.latest_ship_date[0:19], "%Y-%m-%dT%H:%M:%S")))
                        shipment_late_c = first_scan_time_str - latest_ship_date_str
                        if shipment_late_c < 0:
                            shipment_late = 'Y'
                if delivery_time:
                    if val.latest_delivery_date and len(val.latest_delivery_date) >= 20:
                        delivery_time_str = int(time.mktime(delivery_time.timetuple()))
                        latest_delivery_date_str = int(
                            time.mktime(time.strptime(val.latest_delivery_date[0:19], "%Y-%m-%dT%H:%M:%S")))
                        delivery_late_c = delivery_time_str - latest_delivery_date_str
                        if delivery_late_c < 0:
                            delivery_late = 'Y'
            val.status = status
            if first_scan_time:
                val.first_scan_time = first_scan_time
            if delivery_time:
                val.delivery_time = delivery_time
            if shipment_late:
                val.shipment_late = shipment_late
            if delivery_late:
                val.delivery_late = delivery_late
            val.save()

            if val.status == 'Order Processed: Ready for UPS' or val.status == 'Order processed: ready for ups' or val.status == 'Shipment information sent to FedEx':
                data.append({
                    'order_num': val.order_num,
                    'tracking_num': val.tracking_num,
                    'warehouse': val.warehouse,
                    'account_num': val.account_num,
                    'description': val.description,
                    'status': val.status,
                    'shipment_late': val.shipment_late,
                    'delivery_late': val.delivery_late,
                    'billing_date': val.billing_date,
                    'latest_ship_date': val.latest_ship_date,
                    'latest_delivery_date': val.latest_delivery_date,
                    'first_scan_time': val.first_scan_time,
                    'delivery_time': val.delivery_time
                })
        # except Exception as e:
        #     log_obj = StockLogs()
        #     log_obj.id
        #     log_obj.user_id = 1
        #     log_obj.fun = 'tracking 自动更新状态'
        #     log_obj.description = 'Error msg:%s' % (e)
        #     log_obj.save()
        #     continue
    if data:
        fields = [
            '发货单时间',
            '账号',
            'OrderNumber',
            'WarehouseName',
            'Description',
            'Tracking Numbers',
            'latest-ship-date',
            'latest-delivery-date',
            'Status',
            'First Scan time',
            'Delivery time',
            'Shipment Late',
            'Delivery Late'
        ]
        data_fields = [
            'billing_date',
            'account_num',
            'order_num',
            'warehouse',
            'description',
            'tracking_num',
            'latest_ship_date',
            'latest_delivery_date',
            'status',
            'first_scan_time',
            'delivery_time',
            'shipment_late',
            'delivery_late'
        ]
        file_path = get_excel_file1(1, data, fields, data_fields)
        file_path = os.path.join(settings.BASE_DIR, file_path)
        subject = '报告邮件'
        text_content = '未扫描状态的订单汇总。.'
        html_content = '<p>这是一封<strong>未扫描状态的订单汇总</strong>。</p>'
        from_email = settings.DEFAULT_FROM_EMAIL
        msg = EmailMultiAlternatives(subject, text_content, from_email, ['swlxyztd@163.com'])
        msg.attach_alternative(html_content, "text/html")
        # 发送附件
        # text = open(file_path, 'rb').read()
        file_name = os.path.basename(file_path)
        # 对文件进行编码处理
        # b = make_header([(file_name, 'utf-8')]).encode('utf-8')
        # msg.attach(b, text)
        msg.attach_file(file_path)
        msg.send()
        os.remove(file_path)
    t.start()
    pass

@csrf_exempt
def tracking_orders_export(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;', '')
    billing_date_search = request.GET.get('billing_date', '')
    if not billing_date_search:
        billing_date = datetime.datetime.now().strftime("%b.%y")
    else:
        billing_date = time.strptime(billing_date_search, "%Y-%m-%d")
        billing_date = time.strftime('%b.%y', time.localtime(time.mktime(billing_date)))
    if user.user.is_superuser or user.stocks_role == '66':
        lists = TrackingOrders.objects.all()
    else:
        lists = TrackingOrders.objects.filter(user_id=user.user_id)
    if keywords:
        lists = lists.filter(Q(order_num__contains=keywords) | Q(tracking_num__contains=keywords))
    if billing_date:
        lists = lists.filter(billing_date__contains=billing_date)

    data = []
    if lists:
        for val in lists:
            first_scan_time = ''
            delivery_time = ''
            if val.first_scan_time:
                first_scan_time = val.first_scan_time.strftime("%Y-%m-%d %H:%M:%S")
            if val.delivery_time:
                delivery_time = val.delivery_time.strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                'order_num': val.order_num,
                'tracking_num': val.tracking_num,
                'warehouse': val.warehouse,
                'account_num': val.account_num,
                'description': val.description,
                'status': val.status,
                'shipment_late': val.shipment_late,
                'delivery_late': val.delivery_late,
                'billing_date': val.billing_date,
                'latest_ship_date': val.latest_ship_date,
                'latest_delivery_date': val.latest_delivery_date,
                'first_scan_time': first_scan_time,
                'delivery_time': delivery_time
            })

        fields = [
            '发货单时间',
            '账号',
            'OrderNumber',
            'WarehouseName',
            'Description',
            'Tracking Numbers',
            'latest-ship-date',
            'latest-delivery-date',
            'Status',
            'First Scan time',
            'Delivery time',
            'Shipment Late',
            'Delivery Late'
        ]
        data_fields = [
            'billing_date',
            'account_num',
            'order_num',
            'warehouse',
            'description',
            'tracking_num',
            'latest_ship_date',
            'latest_delivery_date',
            'status',
            'first_scan_time',
            'delivery_time',
            'shipment_late',
            'delivery_late'
        ]
        return get_excel_file(request, data, fields, data_fields)
    else:
        return HttpResponse('没有数据~~')