# -*- coding: utf-8 -*-
import os
from maxlead_site.models import UserProfile
from max_stock.models import Menus
from maxlead import settings


class App:
    login_check = ['index']

    def get_user_info(self):
        os.chdir(settings.ROOT_PATH)
        menu_id = self.GET.get('menu_id')
        if not menu_id:
            obj = Menus.objects.filter(url=self.path, parent_id=0)
            if obj:
                menu_id = obj[0].id
        if self.user.id:
            user = UserProfile.objects.get(user_id=self.user.id)
        if not self.user.is_authenticated or user.state == 0:
            return False
        menus = Menus.objects.filter(parent_id=0)
        if menu_id:
            menu_child = Menus.objects.filter(parent_id=menu_id)
        if not user.user.is_superuser and not user.stocks_role == 66:
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
        if menu_id:
            user.menu_child = menu_child
            user.index_menu_id = int(menu_id)
        return user

