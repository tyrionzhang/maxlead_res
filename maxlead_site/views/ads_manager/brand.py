# -*- coding: utf-8 -*-
import json,os
import datetime,csv,codecs
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from maxlead_site.views.app import App
from maxlead_site.models import AdsBrand
from maxlead_site.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from maxlead import settings
from maxlead_site.common.excel_world import handleEncoding

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

@csrf_exempt
def brand(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    viewRange = request.GET.get('viewRange', user.user.id)
    order_type = request.GET.get('order_type', '')
    order_dasc = request.GET.get('order_dasc', '')
    if viewRange:
        viewRange = int(viewRange)
    ads_brand = AdsBrand.objects.all().order_by('-created')
    user_group = user.group
    users = []
    user_list = []
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = UserProfile.objects.filter(state=1)
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        ads_brand = ads_brand.filter(user_id__in=users)

    if viewRange:
        ads_brand = ads_brand.filter(user_id=viewRange)

    if ads_brand:
        for v in ads_brand:
            v.created = v.created.strftime('%Y-%m-%d %H:%M:%S')

    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit

    total_count = len(ads_brand)
    total_page = round(len(ads_brand) / int(limit))
    if int(limit) >= total_count:
        limit = total_count
    if ads_brand:
        paginator = Paginator(ads_brand, limit)
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
            'order_type': order_type,
            'order_dasc': order_dasc,
            'user': user,
            'viewRange': viewRange,
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
    return render(request, 'ads_manager/brand.html', data)

@csrf_exempt
def brand_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        myfile = request.FILES.get('my_file','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        handleEncoding(file_path)
        file = open(file_path, 'r', encoding='UTF-8')
        csv_files = csv.reader(file)
        msg = 'Successfully!\n'
        for i, val in enumerate(csv_files, 0):
            try:
                if i == 0 and not val[0] == 'SKU' and not val[1] == 'ASIN':
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'文件错误~'}),
                                        content_type='application/json')
                if i > 0:
                    brand_check = AdsBrand.objects.filter(user=user.user, sku=val[0], asin=val[1])
                    val[2] = val[2].upper()
                    if brand_check:
                        brand_check.update(brand=val[2])
                    else:
                        brand_obj = AdsBrand()
                        brand_obj.id
                        brand_obj.user = user.user
                        brand_obj.sku = val[0]
                        brand_obj.asin = val[1]
                        brand_obj.brand = val[2]
                        brand_obj.save()
            except:
                msg += '第%s行添加有误。\n' % (i + 1)
                continue
        file.close()
        res = {'code': 1, 'msg': msg}
        os.remove(file_path)
    return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def export_brand(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    brand_data = AdsBrand.objects.all()
    user_group = user.group
    users = []
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = UserProfile.objects.filter(state=1)
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        brand_data = brand_data.filter(user_id__in=users)
    if not brand_data:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在!'}), content_type='application/json')
    file_name = 'brand_%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d')
    data = []
    for val in brand_data:
        data.append([
            val.sku,
            val.asin,
            val.brand
        ])

    response = HttpResponse(content_type='text/csv')  # 设置头信息，告诉浏览器这是个文件
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    writer = csv.writer(response)
    # 先写入columns_name
    writer.writerow(["AKU", "ASIN", "Brand"])
    writer.writerows(data)
    return response

@csrf_exempt
def save_brand(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        id = request.POST.get('id','')
        brand = request.POST.get('brand','')
        brand = brand.upper()
        campaign_obj = AdsBrand.objects.filter(id=id)
        if not campaign_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在！'}), content_type='application/json')
        campaign_obj.update(brand=brand)
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}), content_type='application/json')