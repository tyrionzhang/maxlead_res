# -*- coding: utf-8 -*-
import json,os
import datetime,csv
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import AdsData,AdsCampaign,SearchTeam,Placement,PurProduct,AdvProducts,CampaignPla,KwdPla
from maxlead_site.models import UserProfile,Inventory,BizReport,BrandPerformance,AdsBrand
from maxlead_site.common.excel_world import read_ads_excel, handleEncoding
from django.views.decorators.csrf import csrf_exempt
from maxlead import settings

account_li = {
    1 : u'1账号',
    2 : u'子账号',
    3 : u'2账号',
    4 : u'3账号',
    5 : u'HZ账号',
    6 : u'UKDP'
}

type_li = {
    1 : 'Inventory',
    2 : 'Brand',
    3 : 'Business',
    4 : 'Search Term',
    5 : 'Placement',
    6 : 'Advertised',
    7 : 'Purchased',
    8 : 'SB Camp Pla',
    9 : 'SB Kwd Pla'
}

def data(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    viewRange = request.GET.get('viewRange', user.user.id)
    order_type = request.GET.get('order_type', '')
    order_dasc = request.GET.get('order_dasc', '')
    if viewRange:
        viewRange = int(viewRange)
    ads_data = AdsData.objects.all().order_by('-created')
    user_group = user.group
    users = []
    user_list = []
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = UserProfile.objects.filter(state=1)
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        ads_data = ads_data.filter(user_id__in=users)

    if viewRange:
        ads_data = ads_data.filter(user_id=viewRange)

    if ads_data:
        for v in ads_data:
            range_type_str = ''
            v.is_del = 0
            if not v.change_time:
                check_del = datetime.datetime.now() - v.created
                check_del = check_del.days
                if check_del < 7:
                    v.is_del = 1
                v.change_time = ''
            else:
                v.change_time = v.change_time.strftime('%Y-%m-%d %H:%M:%S')
            if v.month:
                if v.month < 10:
                    range_type_str = "%s0%s" % (v.year_str, v.month)
                else:
                    range_type_str = "%s%s" % (v.year_str, v.month)
            if v.week:
                week_obj = '%s-%s-0' % (v.year_str, v.week)
                start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                start_week_str = start_week + datetime.timedelta(days=-6)
                range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
            v.range_type = range_type_str
            v.created = v.created.strftime('%Y-%m-%d %H:%M:%S')
            v.type = type_li[v.type]
            v.account = account_li[v.account]

    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit

    total_count = len(ads_data)
    total_page = round(len(ads_data) / int(limit))
    if int(limit) >= total_count:
        limit = total_count
    if ads_data:
        paginator = Paginator(ads_data, limit)
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
            'viewRange': viewRange,
            'order_type': order_type,
            'order_dasc': order_dasc,
            'avator': user.user.username[0],
            'user_list': user_list
        }
    else:
        data = {
            'data': '',
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'user': user,
            'viewRange': viewRange,
            'avator': user.user.username[0],
            'user_list': user_list
        }
    return render(request, 'ads_manager/data.html', data)

@csrf_exempt
def data_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        myfile = request.FILES.get('my_file','')
        range_type = request.POST.get('range_type', '')
        week = request.POST.get('week', '')
        month = request.POST.get('month', '')
        account = request.POST.get('account', '')
        type = request.POST.get('type', '')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()

        if type in ['1', '2', '3']:
            if not os.path.isfile(file_path):
                return HttpResponse(json.dumps({'code': 0, 'msg': u'File is not found!'}), content_type='application/json')
            msg = 'Successfully!\n'
            if range_type == 'Monthly':
                month_re = month.split('-')
                year_str = month_re[0]
                month_str = month_re[1]
                week_str = 0
            if range_type == 'Weekly':
                week_re = week.split('-')
                year_str = week_re[0]
                week_str = week_re[1].split('W')[1]
                month_str = 0
            if type == '1':
                file = open(file_path)
                line = file.readline()
                i = 0
                title = line[:8]
                if not title == "sku\tasin":
                    return HttpResponse(json.dumps({'code': 0, 'msg':u'Type与文件不匹配'}), content_type='application/json')
                while line:
                    try:
                        if line and not line[:8] == "sku\tasin":
                            line_re = line.split('\t')
                            # AdsBrand
                            brand_check = AdsBrand.objects.filter(user=user.user, sku=line_re[0])
                            if not brand_check:
                                brand_obj = AdsBrand()
                                brand_obj.id
                                brand_obj.user = user.user
                                brand_obj.sku = line_re[0]
                                brand_obj.asin = line_re[1]
                                brand_obj.save()

                            obj = Inventory()
                            obj.id
                            obj.user = user.user
                            obj.account = account
                            obj.type = type
                            obj.range_type = range_type
                            obj.year_str = year_str
                            obj.sku = line_re[0]
                            obj.asin = line_re[1]
                            if range_type == 'Monthly':
                                obj.month = month_str
                            if range_type == 'Weekly':
                                obj.week = week_str
                            obj.save()
                        line = file.readline()
                    except:
                        line = file.readline()
                        msg += '第%s行添加有误。\n' % (i + 1)
                        continue
            elif type == '2':
                handleEncoding(file_path)
                file = open(file_path, 'r', encoding='UTF-8')
                csv_files = csv.reader(file)
                for i, val in enumerate(csv_files, 0):
                    try:
                        if i == 0 and not val[0] == 'ASIN':
                            return HttpResponse(json.dumps({'code': 0, 'msg': u'Type与文件不匹配'}),
                                                content_type='application/json')
                        if i > 0:
                            # AdsBrand
                            brand_check = AdsBrand.objects.filter(user=user.user, asin=val[0])
                            val[3] = val[3].upper()
                            if brand_check:
                                brand_check.update(brand=val[3])

                            obj = BrandPerformance()
                            obj.id
                            obj.user = user.user
                            obj.account = account
                            obj.type = type
                            obj.range_type = range_type
                            obj.year_str = year_str
                            obj.asin = val[0]
                            obj.brand_name = val[3]
                            if range_type == 'Monthly':
                                obj.month = month_str
                            if range_type == 'Weekly':
                                obj.week = week_str
                            obj.save()
                    except:
                        msg += '第%s行添加有误。\n' % (i + 1)
                        continue
            else:
                handleEncoding(file_path)
                file = open(file_path, 'r', encoding='UTF-8')
                csv_files = csv.reader(file)
                for i, val in enumerate(csv_files, 0):
                    try:
                        if i == 0 and not val[0] == '(Parent) ASIN':
                            return HttpResponse(json.dumps({'code': 0, 'msg': u'Type与文件不匹配'}),
                                                content_type='application/json')
                        if i > 0:
                            # AdsBrand
                            brand_check = AdsBrand.objects.filter(user=user.user, asin=val[1])
                            if brand_check:
                                brand_check.update(parent_asin=val[0])
                            obj = BizReport()
                            obj.id
                            obj.user = user.user
                            obj.account = account
                            obj.type = type
                            obj.range_type = range_type
                            obj.year_str = year_str
                            obj.parent_asin = val[0]
                            obj.asin = val[1]
                            obj.sessions = val[3]
                            obj.page_views = val[5]
                            obj.buy_box_percentage = val[7]
                            obj.units_ordered = val[8]
                            obj.unit_session_percentage = val[10]
                            obj.ordered_product_sales = val[12].split('$')[1].replace(',','')
                            if range_type == 'Monthly':
                                obj.month = month_str
                            if range_type == 'Weekly':
                                obj.week = week_str
                            obj.save()
                    except:
                        msg += '第%s行添加有误。\n' % (i + 1)
                        continue

            file.close()
            data_check = AdsData.objects.filter(user=user.user, account=account, type=type, range_type=range_type,
                                                year_str=year_str, month=month_str, week=week_str)
            if not data_check:
                data_obj = AdsData()
                data_obj.id
                data_obj.user = user.user
                data_obj.account = account
                data_obj.type = type
                data_obj.range_type = range_type
                data_obj.year_str = year_str
                data_obj.month = month_str
                data_obj.week = week_str
                data_id = data_obj.save()
            res = {'code': 1, 'msg': msg}
        else:
            res = read_ads_excel(file_path, user.user, range_type=range_type, week=week, month=month, account=account, type=type)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def del_ads_data(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'GET':
        id = request.GET.get('id', '')
        data_res = AdsData.objects.filter(id=id)
        type = data_res[0].type
        if type == 1:
            model = Inventory
        elif type == 2:
            model = BrandPerformance
        elif type == 3:
            model = BizReport
        elif type == 4:
            model = SearchTeam
        elif type == 5:
            model = Placement
        elif type == 6:
            model = AdvProducts
        elif type == 7:
            model = PurProduct
        elif type == 8:
            model = CampaignPla
        elif type == 9:
            model = KwdPla

        obj = model.objects.filter(user=data_res[0].user, account=data_res[0].account, type=data_res[0].type, range_type=data_res[0].range_type,
                                   year_str=data_res[0].year_str, month=data_res[0].month, week=data_res[0].week)
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not exist!'}), content_type='application/json')
        obj.delete()
        change_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_res.update(change_time=change_time, user=user.user)
        return HttpResponse(json.dumps({'code': 1, 'data': change_time}), content_type='application/json')
