# -*- coding: utf-8 -*-
from django.http import HttpResponse
import xlsxwriter as xlsw
from io import *
import json,time
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
        align = workbook.add_format({'align':'center'})
        for i, val in enumerate(fields,0):
            headings.append(val)
        worksheet1.write_row('A1', headings, bold)

        for c, obj in enumerate(data,2):
            res = []
            if data_fields:
                for v in data_fields:
                    res.append(obj[v])
            if obj['image_names']:
                col_name = ord('A')
                worksheet1.insert_image('%s%s' % (chr(col_name), str(c)), settings.BASE_DIR+'/'+obj['image_names'])
                worksheet1.set_row(c - 1, 45)
                worksheet1.set_column('%s:%s' % (chr(col_name), chr(col_name + 1)), 10)
                col_name += 1
            worksheet1.write_row('B%s' % str(c), res)


        workbook.close()

        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=%s" % file_name

        return response