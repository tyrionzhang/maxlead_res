# -*- coding: utf-8 -*-
import os,json
import base64
from django.contrib import auth
from maxlead_site.models import UserProfile
from max_stock.models import Menus
from maxlead import settings
from django.shortcuts import HttpResponse


class App:
    login_check = ['index']

    def get_user_info(self):
        os.chdir(settings.ROOT_PATH)
        menu_id = self.GET.get('menu_id')
        if not menu_id:
            obj = Menus.objects.filter(url=self.path, parent_id=0)
            if not obj:
                parent = Menus.objects.filter(url=self.path)
                if parent:
                    menu_id = parent[0].parent_id
            if obj:
                menu_id = obj[0].id
        if self.user.id:
            user = UserProfile.objects.get(user_id=self.user.id)
        if not self.user.is_authenticated or user.state == 0:
            return False
        menus = Menus.objects.filter(parent_id=0)
        if menu_id:
            menu_child = Menus.objects.filter(parent_id=menu_id)
        if not user.user.is_superuser and not user.stocks_role == '66':
            menus = menus.filter(roles__code=user.stocks_role)
            if menu_id:
                menu_child = menu_child.filter(roles__code=user.stocks_role)
        if not user.other_email:
            user.other_email = ''
        if not user.email_pass:
            user.email_pass = ''
        if not user.smtp_server:
            user.smtp_server = ''
        user.menu_list = menus
        user.menu_child_type = 0
        if menu_id:
            menu_obj = Menus.objects.get(id=menu_id)
            user.menu_child = menu_child
            user.menu_parent_id = menu_id
            if menu_obj.name == 'Auto Email2':
                user.menu_child_type = 22
            user.index_menu_id = int(menu_id)
        return user

    def get_auth(self):
        if 'HTTP_AUTHORIZATION' in self.META:
            auth_re = self.META.get('HTTP_AUTHORIZATION').split()
            if len(auth_re) != 2:
                return {'status': 400, 'msg': '授权错误'}
            if auth_re[0].lower() != "basic":
                return {'status': 400, 'msg': '授权错误'}
            uname, passwd = base64.b64decode(auth_re[1]).decode().split(':')
            user = auth.authenticate(username=uname, password=passwd)
            if user is None or not user.is_active:
                return {'status': 203, 'msg': '登陆失败/用户错误'}

            return 200
        else:
            return {'status': 400, 'msg': '授权错误'}

