# -*- coding: utf-8 -*-
from django.http import HttpResponse
import xlsxwriter as xlsw
from io import *
import os,time,xlrd,csv,datetime
from django.contrib.auth.models import User
from maxlead_site.models import UserProfile
from max_stock.models import Thresholds
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

def read_excel_file(res):
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

def read_csv_file(res):
    fname = res
    if not os.path.isfile(fname):
        return {'code':0,'msg':'File is not found!'}
    csv_files = csv.reader(open(res,'r'))
    msg = 'Work Is Done!<br>'
    update_fields = ['username', 'email']
    update_fields1 = ['state', 'role', 'group']
    for i,val in enumerate(csv_files,0):
        try:
            if i > 0:
                user = User()
                user.username = val[0]  # 获取第i行中第j列的值
                user.set_password('123456')
                update_fields.append('password')
                user.email = val[1]
                user.id
                user.save()
                if val[4]:
                    group_obj = UserProfile.objects.filter(user__username=val[4])
                else:
                    group_obj = UserProfile.objects.filter(id=1)
                roles = val[3]
                status = val[2]

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
                if roles == 'leader':
                    user_file.group_id = user.userprofile.id
                elif group_obj:
                    user_file.group = group_obj[0]
                else:
                    user_file.group = UserProfile.objects.filter(id=1)[0]

                user_file.save(update_fields=update_fields1)
        except:
            msg += '第%s行添加有误。<br>' % i
            continue
    return {'code': 1, 'msg': msg}


def read_excel_file1(model,res):
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
        str1 = ''
        str2 = ''
        try:
            if i + 1 < nrows:
                for n,val in enumerate(fields,0):
                    if not n == 0:
                        a = '%s,'
                        a1 = "\'%s\',"
                        val_res = table.cell_value(i + 1, n-1,)
                        if n+1 == len(fields):
                            a = '%s'
                            a1 = "\'%s\'"

                        if val.get_internal_type() == 'DateTimeField':
                            val_res = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if val.get_internal_type() == 'DateField':
                            val_res = datetime.datetime.now().strftime("%Y-%m-%d")
                        if val.get_internal_type() == 'IntegerField':
                            a1 = "%s,"
                        str1 += a % val.name
                        str2 += a1  % val_res
                sql = "insert into stock_thresholds (%s) VALUES (%s)" % (str1,str2)
                cursor.execute(sql)
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
                            re_val = int(table.cell_value(i + 1, n - 1, ))
                        re_v.update({val.name:re_val})
                re_data.append(re_v)
    return re_data