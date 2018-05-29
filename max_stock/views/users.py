# -*- coding: utf-8 -*-
import os,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.models import UserProfile
from maxlead_site.common.excel_world import read_excel_file
from maxlead import settings

@csrf_exempt
def userLogin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/admin/max_stock/index/",{'user': request.user})
    return render(request,"Stocks/user/login.html")

@csrf_exempt
def user_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    res = []
    keywords = request.GET.get('keywords', '')
    if user.user.is_superuser:
        res = UserProfile.objects.filter(role=99)
        if keywords:
            res = res.filter(user__username__contains=keywords)
    data = {
        'data':res,
        'title':"UserAdmin",
        'user':user,
    }
    return render(request, "Stocks/user/users.html",data)

@csrf_exempt
def user_save(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        id = request.POST.get('id', '')
        if not id:
            if not username or not password:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Username/Password is empty！'}),
                                    content_type='application/json')
            check = User.objects.filter(username=username)
            if check:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Username is existed！'}),
                                    content_type='application/json')
            user = User()
            user.username = username
            user.set_password(password)
            user.email = request.POST.get('email', '')
            user.id
            user.save()
            user_file = UserProfile()
            user_file.id = user.userprofile.id
            user_file.user_id = user.id
            user_file.role = 99
            user_file.state = 1
            user_file.save()
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Work is done!'}),
                                content_type='application/json')
        else:
            if not username:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Username is empty！'}),
                                    content_type='application/json')
            check = User.objects.filter(username=username).exclude(id=id)
            if check:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Username is existed！'}),
                                                                                content_type='application/json')
            update_fields = ['username', 'email']
            user = User()
            user.username = username
            if password:
                user.set_password(password)
                update_fields.append('password')
            user.email = request.POST.get('email', '')
            user.id=id
            re = user.save(update_fields=update_fields)
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Work is done!'}),
                        content_type='application/json')

@csrf_exempt
def users_import(request):
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
        res = read_excel_file(file_path,'stock')
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def users_del(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        user_obj = User.objects.filter(id=id)
        if not user_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data is not found.'}), content_type='application/json')
        res = user_obj.delete()
        if res:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}), content_type='application/json')

def logout(self):
    auth.logout(self)
    return HttpResponseRedirect("/admin/max_stock/login/")