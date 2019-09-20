# -*- coding: utf-8 -*-
from django.http import HttpResponse
import xlsxwriter as xlsw
from io import *
import os,time,xlrd,csv,datetime
from django.contrib.auth.models import User
from maxlead_site.models import UserProfile
from max_stock.models import SkuUsers,Thresholds,OrderItems,NoSendRes,OldOrderItems,TrackingOrders
from maxlead_site.models import AdsData,AdsCampaign,SearchTeam,Placement,PurProduct,AdvProducts,CampaignPla,KwdPla
from maxlead import settings
from chardet import detect

import pyocr
import importlib
import sys
importlib.reload(sys)
import os.path

from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.converter import PDFPageAggregator, TextConverter
from pdfminer.layout import LTTextBoxHorizontal,LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed


def handleEncoding(original_file):
    with open(original_file, 'rb+') as fp:
        content = fp.read()
        encoding = detect(content)['encoding']
        content = content.decode(encoding).encode('utf8')
        fp.seek(0)
        fp.write(content)

def get_excel_file(self, data,fields,data_fields=[]):

    """
    导出excel表格
    """

    if data:
        headings = []

        file_name = '%s.xlsx' % (time.strftime('%Y-%m-%d %H%M%S'))
        # path_name = settings.DOWNLOAD_URL + '/' + file_name
        # exist_file = os.path.exists(path_name)
        # if exist_file:
        #     os.remove(path_name)
        # 创建工作薄
        output = BytesIO()
        workbook = xlsw.Workbook(output, {'in_memory': True})
        worksheet1 = workbook.add_worksheet(u"Review-Datas")
        bold = workbook.add_format({'bold': 1,'align':'center'})
        for i, val in enumerate(fields,0):
            headings.append(val)
        worksheet1.write_row('A1', headings, bold)

        for c, obj in enumerate(data,2):
            res = []
            if data_fields:
                for v in data_fields:
                    if not v == 'image_names':
                        res.append(obj[v])
            if 'image_names' in obj.keys():
                if obj['image_names']:
                    col_name = ord('A')
                    worksheet1.insert_image('%s%s' % (chr(col_name), str(c)), settings.BASE_DIR+'/'+obj['image_names'])
                    worksheet1.set_row(c - 1, 45)
                    worksheet1.set_column('%s:%s' % (chr(col_name), chr(col_name + 1)), 10)
                    col_name += 1
                worksheet1.write_row('B%s' % str(c), res)

            else:
                worksheet1.write_row('A%s' % str(c), res)


        workbook.close()

        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=%s" % file_name

        return response

def get_excel_file1(self, data,fields,data_fields=[],prefix=''):

    """
    导出excel表格
    """

    if data:
        headings = []

        file_name = '%s%s.xlsx' % (time.strftime('%Y-%m-%d %H%M%S'),prefix)
        path_name1 = settings.DOWNLOAD_URL + '/miner_excel/' + file_name
        dir_path = settings.BASE_DIR + '/'+settings.DOWNLOAD_URL+'miner_excel/'
        path_name = dir_path + file_name
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        exist_file = os.path.exists(path_name)
        if exist_file:
            os.remove(path_name)
        # 创建工作薄
        workbook = xlsw.Workbook(path_name)
        worksheet1 = workbook.add_worksheet(u"Review-Datas")
        bold = workbook.add_format({'bold': 1,'align':'center'})
        for i, val in enumerate(fields,0):
            headings.append(val)
        worksheet1.write_row('A1', headings, bold)

        for c, obj in enumerate(data,2):
            res = []
            if data_fields:
                for v in data_fields:
                    if not v == 'image_names':
                        res.append(obj[v])
            if 'image_names' in obj.keys():
                if obj['image_names']:
                    col_name = ord('A')
                    worksheet1.insert_image('%s%s' % (chr(col_name), str(c)), settings.BASE_DIR+'/'+obj['image_names'])
                    worksheet1.set_row(c - 1, 45)
                    worksheet1.set_column('%s:%s' % (chr(col_name), chr(col_name + 1)), 10)
                    col_name += 1
                worksheet1.write_row('B%s' % str(c), res)

            else:
                worksheet1.write_row('A%s' % str(c), res)


        workbook.close()

        return path_name1

def read_excel_file(res,type=None):
    fname = res
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    data = xlrd.open_workbook(fname)  # 打开fname文件
    data.sheet_names()  # 获取xls文件中所有sheet的名称
    table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
    nrows = table.nrows  # 获取table工作表总行数
    update_fields = ['username', 'email']
    update_fields1 = ['state', 'role', 'group']
    msg = ''
    for i in range(nrows):
        try:
            if i + 1 < nrows:
                user = User()
                user.username = table.cell_value(i + 1, 0, )  # 获取第i行中第j列的值
                user.set_password('123456')
                update_fields.append('password')
                user.email = table.cell_value(i + 1, 1, )
                user.id
                user.save()
                if type == 'stock':
                    user_file = UserProfile()
                    user_file.id = user.userprofile.id
                    user_file.role = 99
                    user_file.state = 1
                    user_file.save(update_fields=['role'])
                else:
                    if table.cell_value(i + 1, 4, ):
                        group_obj = UserProfile.objects.filter(user__username=table.cell_value(i + 1, 4, ))
                    else:
                        group_obj = UserProfile.objects.filter(id=1)
                    roles = table.cell_value(i + 1, 3, )
                    status = table.cell_value(i + 1, 2, )

                    user_file = UserProfile()
                    user_file.id = user.userprofile.id
                    user_file.user_id = user.id

                    if roles == 'member':
                        user_file.role = 0
                    elif roles == 'leader':
                        user_file.role = 1
                    else:
                        user_file.role = 2
                    if status == 'active':
                        user_file.state = 1
                    else:
                        user_file.state = 0
                    if group_obj:
                        user_file.group = group_obj[0]
                    else:
                        user_file.group = UserProfile.objects.filter(id=1)[0]

                    user_file.save(update_fields=update_fields1)
        except:
            msg += '第%s行添加有误。<br>' % i
            continue
    return {'code': 1, 'msg': msg}

def read_csv_file(model,res,user, email=None, expired_time=None, customer_num=None):
    fname = res
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    handleEncoding(res)
    csv_files = csv.reader(open(res,'r', encoding='UTF-8'))
    msg = 'Work Is Done!<br>'
    querysetlist = []
    try:
        for i,val in enumerate(csv_files,0):
            try:
                if i > 0:
                    email_address = val[28]
                    if not email_address:
                        email_address = val[30]
                    if not email_address:
                        email_address = val[28]
                    if email_address and not email_address.find('myContacts') == -1:
                        email_address = val[0]
                    mail_add_num = email_address.find('+')
                    if email_address and not email_address.find('marketplace.amazon.com') == -1 and not mail_add_num == -1:
                        email_address = "%s@marketplace.amazon.com" % email_address[0:mail_add_num]

                    email_address = email_address.strip()
                    checks = model.objects.filter(email_address=email_address, expired_time__gt=datetime.datetime.now())
                    if checks:
                        continue
                    checks2 = model.objects.filter(email_address=email_address, expired_time__lt=datetime.datetime.now())
                    if checks2:
                        checks2.delete()
                    querysetlist.append(model(email_address=email_address,user_id=user.user.id, expired_time=expired_time,email=email,customer_num=customer_num))
            except:
                msg += '第%s行添加有误。<br>' % i
                continue
    except:
        pass
    if querysetlist:
        model.objects.bulk_create(querysetlist)
    return {'code': 1, 'msg': msg}


def read_excel_file1(model,res,model_name,user=None,customer_num=None):
    from django.db import connection, transaction
    cursor = connection.cursor()
    fname = res
    msg = ''
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    data = xlrd.open_workbook(fname)  # 打开fname文件
    data.sheet_names()  # 获取xls文件中所有sheet的名称
    table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
    nrows = table.nrows
    fields = model._meta.fields
    for i in range(nrows):
        str1 = ""
        str2 = ""
        try:
            if i + 1 < nrows:
                if model_name == 'sku_users':
                    user_name = table.cell_value(i + 1, 0,)
                    sku = table.cell_value(i + 1, 1,)
                    check = SkuUsers.objects.filter(user__username=user_name,sku=sku)
                    if check:
                        msg += '第%s行已存在。<br>' % (i + 1)
                        continue
                if model_name == 'stock_thresholds':
                    sku = table.cell_value(i + 1, 0, )
                    warehouse = table.cell_value(i + 1, 1, )
                    check = Thresholds.objects.filter(sku=sku,warehouse=warehouse)
                    if check:
                        msg += '第%s行已存在。<br>' % (i + 1)
                        continue

                if model_name == 'no_send_res':
                    order_id = table.cell_value(i + 1, 1, )
                    sku = table.cell_value(i + 1, 2, )
                    sku = sku.strip()
                    check = NoSendRes.objects.filter(sku=sku, order_id=order_id)
                    if check:
                        msg += '第%s行已存在。<br>' % (i + 1)
                        continue

                for n,val in enumerate(fields,0):
                    if n == 1 and user:
                        a = '%s,'
                        a1 = "\'%s\',"
                        val_res = user
                        val.name = 'user_id'
                        str1 += a % val.name
                        str2 += a1 % val_res
                    elif customer_num and n == 2:
                        a = '%s,'
                        a1 = "\'%s\',"
                        str1 += a % 'customer_num'
                        str2 += a1 % customer_num
                    elif not n == 0:
                        a = '%s,'
                        a1 = "\'%s\',"
                        if user:
                            if customer_num:
                                val_res = table.cell_value(i + 1, n - 3, )
                            else:
                                val_res = table.cell_value(i + 1, n-2,)
                        else:
                            val_res = table.cell_value(i + 1, n - 1, )
                        if n+1 == len(fields):
                            a = '%s'
                            a1 = "\'%s\'"
                        if val.name == 'user_id' or val.name == 'user':
                            user_obj = User.objects.filter(username=val_res)
                            if user_obj:
                                val_res = user_obj[0].id
                                val.name = 'user_id'
                        if val.name == 'send_time':
                            try:
                                val_res = xlrd.xldate.xldate_as_datetime(val_res, 0).strftime("%H:%M")
                            except:
                                pass
                        if val.get_internal_type() == 'DateTimeField':
                            if not val_res:
                                val_res = datetime.datetime.now()
                            else:
                                if model_name == 'no_send_res':
                                    val_res = datetime.datetime.now()
                                else:
                                    val_res = xlrd.xldate.xldate_as_datetime(val_res, 0)
                        if val.get_internal_type() == 'DateField':
                            if not val_res:
                                val_res = datetime.datetime.now().strftime("%Y-%m-%d")
                            else:
                                val_res = xlrd.xldate.xldate_as_datetime(val_res, 0)
                        if val.get_internal_type() == 'IntegerField':
                            a1 = "%s,"
                        if val.get_internal_type() == 'TextField':
                            val_res = val_res.replace("'","/")
                        str1 += a % val.name
                        str2 += a1  % val_res
                sql = "insert into %s (%s) VALUES (%s)" % (model_name,str1,str2)
                cursor.execute(sql)
        except:
            msg += '第%s行添加有误。<br>' % (i+1)
            continue
    return {'code': 1, 'msg': msg}

def read_excel_for_orders(res,user=None,customer_num=None):
    fname = res
    msg = ''
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    data = xlrd.open_workbook(fname)  # 打开fname文件
    data.sheet_names()  # 获取xls文件中所有sheet的名称
    table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
    nrows = table.nrows
    for i in range(nrows):
        try:
            if i + 1 < nrows:
                payments_date = table.cell_value(i + 1, 3,)
                order_id = table.cell_value(i + 1, 0,).strip()
                checks = OldOrderItems.objects.filter(order_id=order_id)
                if not checks:
                    obj = OrderItems()
                    obj.id
                    if user:
                        obj.user_id = user
                    obj.customer_num = customer_num
                    obj.order_id = order_id
                    obj.sku = table.cell_value(i + 1, 7,).strip()
                    if not obj.sku:
                        obj.sku = table.cell_value(i + 1, 8,).strip()
                    obj.order_status = 0
                    obj.email = table.cell_value(i + 1, 4,)
                    obj.customer = table.cell_value(i + 1, 5,)
                    if payments_date:
                        obj.payments_date = table.cell_value(i + 1, 3,)
                    obj.save()

        except:
            msg += '第%s行添加有误。<br>' % (i+1)
            continue
    return {'code': 1, 'msg': msg}

def read_excel_data(model,res):
    fname = res
    re_data = []
    if os.path.isfile(fname):
        data = xlrd.open_workbook(fname)  # 打开fname文件
        data.sheet_names()  # 获取xls文件中所有sheet的名称
        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
        nrows = table.nrows
        if not model == 1:
            fields = model._meta.fields
        for i in range(nrows):
            re_v = {}
            if i + 1 < nrows:
                if not model == 1:
                    for n,val in enumerate(fields,0):
                        try:
                            if not n == 0:
                                re_val = table.cell_value(i + 1, n-1,)
                                if val.get_internal_type() == 'CharField':
                                    re_val = re_val.strip()
                                if val.get_internal_type() == 'DateTimeField':
                                    re_val = xlrd.xldate.xldate_as_datetime(re_val, 0).strftime("%Y-%m-%d %H:%M:%S")
                                    if not re_val:
                                        re_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if val.get_internal_type() == 'DateField':
                                    re_val = xlrd.xldate.xldate_as_datetime(re_val, 0).strftime("%Y-%m-%d")
                                    if not re_val:
                                        re_val = datetime.datetime.now().strftime("%Y-%m-%d")
                                if val.get_internal_type() == 'IntegerField':
                                    if not re_val:
                                        re_val = val.default
                                    else:
                                        re_val = int(re_val)
                                re_v.update({val.name:re_val})
                        except:
                            continue
                    re_data.append(re_v)
                else:
                    re_v.update({
                        'sku' : table.cell_value(i + 1, 0,),
                        'exl' : int(table.cell_value(i + 1, 1,)),
                        'twu' : int(table.cell_value(i + 1, 2,)),
                        'ego' : int(table.cell_value(i + 1, 3,)),
                        'tfd' : int(table.cell_value(i + 1, 4,)),
                        'hanover' : int(table.cell_value(i + 1, 5,)),
                        'atl' : int(table.cell_value(i + 1, 6,)),
                        'pc' : int(table.cell_value(i + 1, 7,)),
                        'zto' : int(table.cell_value(i + 1, 8,)),
                        'date' : xlrd.xldate.xldate_as_datetime(table.cell_value(i + 1, 7,), 0)
                    })
                    re_data.append(re_v)
    return re_data

def read_excel_for_tracking_orders(res,user=None):
    fname = res
    msg = ''
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    data = xlrd.open_workbook(fname)  # 打开fname文件
    data.sheet_names()  # 获取xls文件中所有sheet的名称
    table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
    nrows = table.nrows
    for i in range(nrows):
        if i + 1 < nrows:
            try:
                tracking_num = table.cell_type(i + 1, 5, )
                if tracking_num == 2:
                    tracking_num = int(table.cell_value(i + 1, 5, ))
                else:
                    tracking_num = table.cell_value(i + 1, 5, )
                order_num = table.cell_type(i + 1, 2, )
                if order_num == 2:
                    order_num = int(table.cell_value(i + 1, 2, ))
                else:
                    order_num = table.cell_value(i + 1, 2, )
                checks = TrackingOrders.objects.filter(tracking_num=tracking_num, order_num=order_num)
                if not checks:
                    obj = TrackingOrders()
                    obj.id
                    if user:
                        obj.user_id = user
                    obj.billing_date = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y') + table.cell_value(i + 1, 0, ), "%Y%b.%d")
                    obj.account_num = table.cell_value(i + 1, 1, )
                    obj.order_num = order_num
                    obj.warehouse = table.cell_value(i + 1, 3, )
                    obj.description = table.cell_value(i + 1, 4, ).strip()
                    obj.tracking_num = tracking_num
                    obj.latest_ship_date = table.cell_value(i + 1, 6,)
                    obj.latest_delivery_date = table.cell_value(i + 1, 7,)
                    obj.save()
                else:
                    msg += '第%s行已存在。<br>' % (i + 1)
            except:
                msg += '第%s行添加有误。<br>' % (i + 1)
                continue
    return {'code': 1, 'msg': msg}

def readPDF(pdfFile):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)

    process_pdf(rsrcmgr, device, pdfFile)
    device.close()

    content = retstr.getvalue()
    retstr.close()
    # 获取所有行
    lines = str(content).split("\n")
    return content

def read_excel_data_for_pdf(model,res):
    fields = model._meta.fields
    '''解析PDF文本'''
    fp = open(res, 'rb')
    outputString = readPDF(fp)
    print(outputString)
    # 用文件对象创建一个PDF文档分析器
    parser = PDFParser(fp)
    # 创建一个PDF文档
    doc = PDFDocument()
    # 连接分析器，与文档对象
    parser.set_document(doc)
    doc.set_parser(parser)

    # 提供初始化密码，如果没有密码，就创建一个空的字符串
    doc.initialize()

    # 检测文档是否提供txt转换，不提供就忽略
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 创建PDF，资源管理器，来共享资源
        rsrcmgr = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        # 创建一个PDF解释其对象
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        # 循环遍历列表，每次处理一个page内容
        # doc.get_pages() 获取page列表
        for page in doc.get_pages():
            interpreter.process_page(page)
            # 接受该页面的LTPage对象
            layout = device.get_result()
            # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象
            # 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等
            # 想要获取文本就获得对象的text属性，
            for x in enumerate(layout, 0):
                if (isinstance(x, LTTextBoxHorizontal)):
                    results = x.get_text()
                    print(results)


def read_ads_excel(file, user, range_type=None, week=None, month=None, account=None, type=None):
    from django.db import connection, transaction
    cursor = connection.cursor()
    msg = 'Successfully!\n'
    if os.path.isfile(file):
        data = xlrd.open_workbook(file)  # 打开fname文件
        data.sheet_names()  # 获取xls文件中所有sheet的名称
        table = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
        type_check = table.cell_value(0, 13, )
        if type == '4':
            if not type_check == 'Spend':
                msg = u'Type与文件不匹配'
                return msg
            model = SearchTeam
            fields = model._meta.fields
        elif type == '5':
            if not type_check == 'Total Return on Advertising Spend (RoAS)':
                msg = u'Type与文件不匹配'
                return msg
            model = Placement
            fields = model._meta.fields
        elif type == '7':
            if not type_check == '7 Day Other SKU Sales ':
                msg = u'Type与文件不匹配'
                return msg
            model = PurProduct
            fields = model._meta.fields
        elif type == '6':
            if not type_check == '7 Day Total Sales ':
                msg = u'Type与文件不匹配'
                return msg
            model = AdvProducts
            fields = model._meta.fields
        elif type == '8':
            if not type_check == '14 Day Total Sales ':
                msg = u'Type与文件不匹配'
                return msg
            model = CampaignPla
            fields = model._meta.fields
        elif type == '9':
            if not type_check == 'Total Advertising Cost of Sales (ACoS) ':
                msg = u'Type与文件不匹配'
                return msg
            model = KwdPla
            fields = model._meta.fields

        nrows = table.nrows
        if range_type == 'Monthly':
            month = month.split('-')
            year_str = month[0]
            month = month[1]
            week = 0
        if range_type == 'Weekly':
            week = week.split('-')
            year_str = week[0]
            week = week[1].split('W')[1]
            month = 0

        for i in range(1, nrows):
            try:
                # AdsCampaign
                campaign_check = AdsCampaign.objects.filter(user=user, campaign=table.cell_value(i, 4, ), account=account)
                if not campaign_check:
                    campaign_obj = AdsCampaign()
                    campaign_obj.id
                    campaign_obj.campaign = table.cell_value(i, 4, )
                    campaign_obj.user = user
                    campaign_obj.account = account
                    campaign_obj.save()
                field_str = ''
                value_str = "'%s', '0', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s',"
                value_str = value_str % (user.id, account, type, range_type, year_str, month, week, table.cell_value(i, 2, ).
                                         replace("'", "|"), table.cell_value(i, 4, ))
                for n, val in enumerate(fields, 0):
                    if 0 < n < len(fields):
                        if n == 1:
                            val.name = 'user_id'
                        if n == (len(fields) - 1):
                            field_str += val.name
                        else:
                            field_str += val.name + ','
                        if n > 10:
                            if n == (len(fields) - 1):
                                val_str = "\'%s\'"
                                val_str = val_str % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                table_val = table.cell_value(i, n - 6, )
                                if isinstance(table_val, str):
                                    table_val = table.cell_value(i, n - 6, ).replace("'", "|")
                                val_str = "\'%s\',"
                                val_str = val_str % table_val
                            value_str += val_str
                sql = 'insert into %s (%s) VALUES (%s)' % (model._meta.db_table, field_str, value_str)
                cursor.execute(sql)
            except:
                msg += '第%s行添加有误。\n' % (i + 1)
                continue
        data_check = AdsData.objects.filter(user=user, account=account, type=type, range_type=range_type, year_str=year_str,
                                            month=month, week=week, change_time=None)
        if not data_check:
            data_obj = AdsData()
            data_obj.id
            data_obj.user = user
            data_obj.account = account
            data_obj.type = type
            data_obj.range_type = range_type
            data_obj.year_str = year_str
            data_obj.month = month
            data_obj.week = week
            data_id = data_obj.save()
    return {'code': 1, 'msg': msg}
