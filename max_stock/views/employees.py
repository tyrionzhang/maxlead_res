# -*- coding: utf-8 -*-
import os,json
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.models import UserProfile,Employee

@csrf_exempt
def init(request):
    users = UserProfile.objects.all()
    for va in users:
        employee = Employee()
        employee.user_id = va.user_id
        employee.name = va.user.username
        employee.save()
    return render(request, "Stocks/user/users.html")

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    keywords = request.GET.get('keywords', '').replace('amp;', '')
    lists = Employee.objects.filter(parent_user=user.user_id).order_by('name', 'id')
    all_lists = Employee.objects.all().exclude(user__is_superuser=1).exclude(user_id=user.user_id).order_by('name', 'id')
    if user.user.is_superuser or user.stocks_role == '66':
        lists = all_lists
    if keywords:
        lists = lists.filter(user__username__contains=keywords)
    for val in lists:
        parent_user = UserProfile.objects.filter(user_id=val.parent_user)
        if parent_user:
            val.parent = parent_user[0].user.username
        else:
            val.parent = ''
    for v in all_lists:
        if v.parent_user == user.user_id:
            v.check_employee = 1

    data = {
        'user': user,
        'data': lists,
        'all_lists': all_lists,
        'keywords': keywords,
        'title': 'employee',
    }
    return render(request, "Stocks/employee/index.html", data)

@csrf_exempt
def save(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        name = request.POST.get('name','')
        parent_user = request.POST.get('parent_user','')
        if id:
            if not name:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'The name cannot be empty!'}),
                                    content_type='application/json')
            emp = Employee.objects.filter(id=int(id))
            if emp:
                check = Employee.objects.filter(name=name).exclude(id=id)
                if check:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Data already exists!'}),
                                        content_type='application/json')
                emp.update(name=name)
        else:
            if name:
                check = Employee.objects.filter(name=name)
                check_user = User.objects.filter(username=name)
                if check or check_user:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'Data already exists!'}),
                                        content_type='application/json')
                emp_user = User()
                emp_user.id
                emp_user.username = name
                emp_user.set_password('123456')
                emp_user.save()
                emp_obj = Employee()
                emp_obj.id
                emp_obj.user_id = emp_user.id
                emp_obj.name = name
                emp_obj.parent_user = parent_user
                emp_obj.save()
    return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}),
                        content_type='application/json')

@csrf_exempt
def delete(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        obj = Employee.objects.filter(id=id)
        user_obj = User.objects.filter(id=obj[0].user_id)
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Data already exists!'}),
                                content_type='application/json')
        if(obj.delete()):
            user_obj.delete()
            return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}),
                                content_type='application/json')

@csrf_exempt
def edit_children(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        child_employee = request.POST.get('child_employee', '')
        child_obj = Employee.objects.filter(parent_user=user.user_id)
        if child_obj:
            child_obj.update(parent_user=0)
        if child_employee:
            child_employees = Employee.objects.filter(id__in=eval(child_employee))
            if child_employees:
                child_employees.update(parent_user=user.user_id)

        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}),
                                content_type='application/json')
