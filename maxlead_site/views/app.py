# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from maxlead_site.models import UserProfile


class App:
    login_check = ['index']

    def get_user_info(self):
        if self.user.id:
            user = UserProfile.objects.get(user_id=self.user.id)
        if not self.user.is_authenticated() or user.state == 0:
            return False
        return user

