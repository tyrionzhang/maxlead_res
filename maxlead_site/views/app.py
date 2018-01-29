# -*- coding: utf-8 -*-
import os
from maxlead_site.models import UserProfile
from maxlead import settings


class App:
    login_check = ['index']

    def get_user_info(self):
        os.chdir(settings.ROOT_PATH)
        print(self.user)
        if self.user.id:
            user = UserProfile.objects.get(user_id=self.user.id)
        if not self.user.is_authenticated() or user.state == 0:
            return False
        return user

