from django.http import HttpResponse
from xlwt import *
from io import *
import os,time
from django.contrib import admin
from maxlead_site.models import UserAsins,AsinReviews,Reviews
from maxlead import settings

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
        res = list(queryset.all().values())
        # 创建工作薄
        ws = Workbook(encoding='utf-8')
        w = ws.add_sheet(u"数据报表第一页")
        for i, val in enumerate(obj_items[0],0):
            w.write(0, i, val)

        # 写入数据
        excel_row = 1
        for obj in res:
            for k, field in enumerate(obj_items[1],0):
                if field == 'review_date' or field == 'created':
                    field = str(obj[field].year)+'-'+str(obj[field].month)+'-'+str(obj[field].day)
                else:
                    field = obj[field]

            # dada_review_date = str(obj['review_date'].year)+'-'+str(obj['review_date'].month)+'-'+str(obj['review_date'].day)
            # dada_created = str(obj['created'].year)+'-'+str(obj['created'].month)+'-'+str(obj['created'].day)
                w.write(excel_row, k, field)
            excel_row += 1
            # 检测文件是够存在
        # 方框中代码是保存本地文件使用，如不需要请删除该代码
        ###########################
        file_name = '%s-%s.xls' % (self.model._meta.db_table, time.strftime('%Y-%m-%d-%H%M%S'))
        path_name = settings.DOWNLOAD_URL+'/'+file_name

        exist_file = os.path.exists(path_name)
        if exist_file:
            os.remove(path_name)
        ws.save(path_name)
        ############################
        sio = BytesIO()
        ws.save(sio)
        sio.seek(0)
        response = HttpResponse(sio.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        response.write(sio.getvalue())
        return response
get_excel_file.short_description = "下载数据表"

@admin.register(UserAsins)
class UserAsinsAdmin(admin.ModelAdmin):
    list_display=('id', 'user', 'aid', 'name')

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