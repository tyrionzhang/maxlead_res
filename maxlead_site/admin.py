# -*- coding: utf-8 -*-
from django.http import HttpResponse
import xlsxwriter as xlsw
from io import *
import json,time
from django.contrib import admin
from maxlead_site.models import UserAsins,AsinReviews,Reviews,UserProfile,MenberGroups

# Register your models here.

def getmodelfield(self):
    fielddic=[]
    verbose_names = []
    field_names = []
    for field in self.model._meta.fields:
        field_names.append(field.name)
        verbose_names.append(field.verbose_name)
    fielddic.append(verbose_names)
    fielddic.append(field_names)
    return fielddic

def get_excel_file(self, request, queryset):

    """
    导出excel表格
    """
    obj_items = getmodelfield(self)

    if queryset:
        headings = []
        res = list(queryset.all().values())

        file_name = '%s-%s.xlsx' % (self.model._meta.db_table, time.strftime('%Y-%m-%d-%H%M%S'))
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
        for i, val in enumerate(obj_items[0],0):
            if not val == 'Image Urls':
                headings.append(val)
        worksheet1.write_row('A1', headings, bold)

        for c, obj in enumerate(res,2):
            data = []
            for k, field in enumerate(obj_items[1],2):
                if field == 'review_date' or field == 'created':
                    field = str(obj[field].year)+'-'+str(obj[field].month)+'-'+str(obj[field].day)
                else:
                    field = obj[field]
                data.append(field)
            worksheet1.write_row('A%s' % str(c), data, align)
            if obj['image_names']:
                imgs = obj['image_names'].split('||')
                col_name = ord('L')
                for img in imgs:
                    if img:
                        worksheet1.insert_image('%s%s' % (chr(col_name),str(c)), img)
                        worksheet1.set_row(c-1,70)
                        worksheet1.set_column('%s:%s' % (chr(col_name),chr(col_name+1)), 20)
                    col_name += 1
                        # if obj['name'] == 'Emory Daniels':
            #     worksheet1.insert_image('L%s' % str(c), 'C:\\Users\\asus\\Pictures\\Camera Roll\\timg1.jpg')

        workbook.close()

        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=%s" % file_name

        return response

get_excel_file.short_description = "下载数据表"

@admin.register(UserAsins)
class UserAsinsAdmin(admin.ModelAdmin):
    list_display=('id', 'user', 'aid', 'review_watcher', 'listing_watcher', 'is_use')

    list_per_page = 15

    ordering = ('-id',)

    # list_editable 设置默认可编辑字段
    # list_editable = ['author']

    # fk_fields 设置显示外键字段
    # fk_fields = ('machine_room_id',)

    # 设置哪些字段可以点击进入编辑界面
    # list_display_links = ('id', 'text')
    # 筛选器
    # list_filter = ('trouble', 'go_time', 'act_man__user_name', 'machine_room_id__machine_room_name')  # 过滤器
    search_fields = ('aid', 'name')  # 搜索字段
    # date_hierarchy = 'go_time'  # 详细时间分层筛选　

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id','state')
    fields = ('user','state','group')
    filter_horizontal = ('group',)

@admin.register(MenberGroups)
class MenberGroupsAdmin(admin.ModelAdmin):
    list_display = ('id','name','created')
    fields = ('name',)
    fk_fields = ('name',)

@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'asin', 'title', 'score', 'review_date', 'created')

    list_per_page = 15

    ordering = ('-id',)

    search_fields = ('content', 'asin')  # 搜索字段

    list_filter = ('created', 'review_date', 'is_vp')

    actions = [get_excel_file]

@admin.register(AsinReviews)
class AsinReviewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'aid', 'avg_score','total_review', 'created')

    list_per_page = 15

    ordering = ('-id',)

    search_fields = ('positive_keywords', 'negative_keywords','aid')  # 搜索字段

    actions = [get_excel_file]