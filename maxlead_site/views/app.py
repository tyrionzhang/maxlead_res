# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from maxlead_site.models import UserProfile


class App:
    login_check = ['index']

    def get_user_info(self):
        if not self.user.is_authenticated():
            return False
        user = UserProfile.objects.get(user_id=self.user.id)
        return user

