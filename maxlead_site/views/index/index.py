# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.shortcuts import render
from maxlead_site.views.app import App

class Index:

    def index(self):
        user = App.get_user_info(self)
        if not user:
            return  HttpResponseRedirect('/admin/maxlead_site/login')
        return render(self, "index/index.html",{'user': user,'avator':user.user.username[0]})