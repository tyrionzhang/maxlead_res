# -*- coding: utf-8 -*-
import os
from maxlead_site.models import UserProfile
from max_stock.models import Menus
from maxlead import settings


class App:
    login_check = ['index']

    def get_user_info(self):
        os.chdir(settings.ROOT_PATH)
        if self.user.id:
            user = UserProfile.objects.get(user_id=self.user.id)
        if not self.user.is_authenticated or user.state == 0:
            return False
        menus = Menus.objects.all()
        if not user.user.is_superuser and not user.stocks_role == 66:
            menus = menus.filter(roles__code=user.stocks_role)
        user.menu_list = menus
        return user

