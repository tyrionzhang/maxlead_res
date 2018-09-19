# -*- coding: utf-8 -*-
from django.http import HttpResponse
import xlsxwriter as xlsw
from io import *
import os,time,xlrd,csv,datetime
from django.contrib.auth.models import User
from maxlead_site.models import UserProfile
from max_stock.models import SkuUsers,Thresholds,OrderItems,NoSendRes
from maxlead import settings

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

def read_csv_file(model,res,email=None, expired_time=None):
    fname = res
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    csv_files = csv.reader(open(res,'r', encoding='UTF-8'))
    msg = 'Work Is Done!<br>'
    querysetlist = []
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

                checks = model.objects.filter(email_address=email_address, expired_time__gt=datetime.datetime.now())
                if checks:
                    continue
                checks2 = model.objects.filter(email_address=email_address, expired_time__lt=datetime.datetime.now())
                if checks2:
                    checks2.delete()
                querysetlist.append(model(email_address=email_address,expired_time=expired_time,email=email))
        except:
            msg += '第%s行添加有误。<br>' % i
            continue
    if querysetlist:
        model.objects.bulk_create(querysetlist)
    return {'code': 1, 'msg': msg}


def read_excel_file1(model,res,model_name,user=None):
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
        # try:
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
                elif not n == 0:
                    a = '%s,'
                    a1 = "\'%s\',"
                    if user:
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
                        val_res = xlrd.xldate.xldate_as_datetime(val_res, 0).strftime("%H:%M")
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
        # except:
        #     msg += '第%s行添加有误。<br>' % (i+1)
        #     continue
    return {'code': 1, 'msg': msg}

def read_excel_for_orders(res,user=None):
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
                obj = OrderItems()
                obj.id
                if user:
                    obj.user_id = user
                obj.order_id = table.cell_value(i + 1, 0,)
                obj.sku = table.cell_value(i + 1, 7,)
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
        fields = model._meta.fields
        for i in range(nrows):
            re_v = {}
            if i + 1 < nrows:
                for n,val in enumerate(fields,0):
                    if not n == 0:
                        re_val = table.cell_value(i + 1, n-1,)
                        if val.get_internal_type() == 'CharField':
                            re_val = re_val.strip()
                        if val.get_internal_type() == 'DateTimeField':
                            re_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if val.get_internal_type() == 'DateField':
                            re_val = datetime.datetime.now().strftime("%Y-%m-%d")
                        if val.get_internal_type() == 'IntegerField':
                            if not re_val:
                                re_val = val.default
                            else:
                                re_val = int(re_val)
                        re_v.update({val.name:re_val})
                re_data.append(re_v)
    return re_data