# -*- coding: utf-8 -*-
import time,os
from django.contrib import auth
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from maxlead_site.models import UserProfile,MenberGroups
from maxlead import settings
from maxlead_site.common.prpcrypt import Prpcrypt
from maxlead_site.views import commons
from maxlead_site.views.app import App


class Logins:
    role = ['member','Leader','admin']

    @csrf_exempt
    def userLogin(self):
        if self.user.is_authenticated():
            return HttpResponseRedirect("/admin/maxlead_site/index/",{'user': self.user,'avator':self.user.username[0]})
        if self.method == 'POST':
            username = self.POST.get('username', '')
            password = self.POST.get('password', '')
            user = auth.authenticate(username=username, password=password)
            if not user:
                return {'code': 0, 'msg': u'账号/密码错误，请确认后重试！'}
            user1 = User.objects.get(username=username)
            user_file = UserProfile.objects.filter(user=user1.id)
            if user_file[0].state in (0,2):
                return {'code': 0, 'msg': u'账号不存在/已被锁定,请联系管理员！'}

            if user.is_active and user_file[0].state == 1:
                user_file.update(er_count=0,em_count=0)
                auth.login(self, user)
                self.session.set_expiry(604800) # 登陆状态生命
                commons.loger(description='用户登陆正常',user=user,name='用户登陆')
                return HttpResponseRedirect("/admin/maxlead_site/index/",{'user': user,'avator':user.username[0]})
            else:
                if user_file[0].em_count >= 5:
                    return {'code': 0, 'msg': u'密码错误超过5次，账号已被锁定'}
                er_count = user_file[0].er_count+1
                now_time = int(time.time())
                user_file.update(er_count=er_count,er_time=now_time)
                if er_count>=5 and now_time-user_file[0].er_time<=86400:
                    user_file.update(state=2) #2,账号锁定
                    return {'code': 0, 'msg': u'密码错误超过5次，账号已被锁定'}

        return render(self,"user/signin.html")

    def logout(self):
        auth.logout(self)
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    @csrf_exempt
    def forget_password_for_email(self):
        username = self.POST.get('name', '')
        email = self.POST.get('email', '')
        user = User.objects.get(username=username,email=email)

        if not user:
            user_file = UserProfile.objects.filter(user=user.id)
            if user_file[0].em_count>=5:
                return {'code':0,'msg':u'连续输入错误邮箱超过5次，账号已被锁定'}
            em_count = user_file[0].em_count + 1
            now_time = int(time.time())
            user_file.update(em_count=em_count, er_time=now_time)
            if em_count >= 5 and now_time - user_file[0].er_time <= 86400:
                user_file.update(state=2)  # 2,
                return {'code': 0, 'msg': u'连续输入错误邮箱超过5次，账号已被锁定'}
            return {'code':0, 'msg':'邮箱有误！'}

        url = '%s/admin/maxlead_site/reset_pass?key_words=%s&did=%s'
        key_words = Prpcrypt.encrypt(self,text=username + '||' + email)
        now_time = int(time.time())
        urls = url % (settings.ROOT_URL,key_words,Prpcrypt.encrypt(self,text=str(now_time)))
        subject = 'Maxlead账户密码找回'
        msg = '''
%s，您好！
    下面是您的密码重置链接，请在3分种内点击修改密码，谢谢！%s
        ''' % (username,urls)
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, msg, from_email, [email], fail_silently=False)
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    def email_reset_pass(self):
        key_words = self.GET['key_words']
        did = self.GET['did']
        if key_words and did:
            key_words = Prpcrypt.decrypt(self,key_words)
            did = Prpcrypt.decrypt(self,did)
            now_time = int(time.time())
            if now_time - int(did) < 180 and key_words:
                username = key_words.split('||')[0]
                url = "/admin/maxlead_site/reset_pass?username=%s&did=%s" % (Prpcrypt.encrypt(self,username),Prpcrypt.encrypt(self,username+settings.KEY_STR))
                return HttpResponseRedirect(url)
            else:
                return render(self, 'error/login_error.html', {'msg': 'url地址已过期/参数有误！'})
        else:
            return render(self, 'error/login_error.html', {'msg': 'url地址参数有误！'})

    @csrf_exempt
    def save_user(self):
        users = self.user
        if users.is_authenticated():
            user_file = UserProfile.objects.get(user=users.id)
            user_id = self.POST.get('id', '')
            group = self.POST.get('group', '')
            if isinstance(group, str) or isinstance(group, int):
                group = [int(group)]
            if user_file.role == 2:
                user = User()
                if user_id:
                    user.id = user_id
                else:
                    user.id
                user.username = self.POST.get('name', '')
                user.set_password(self.POST.get('password', ''))
                user.email = self.POST.get('email', '')

                user.save()

                user_file = UserProfile()
                user_file.id = user.userprofile.id
                user_file.user_id = user.id
                user_file.state = self.POST.get('state', '')
                user_file.role = self.POST.get('role', '')
                user_file.save()

                for val in group:
                    if user_id:
                        user_file.group.remove(val)
                    user_file.group.add(val)

                return render(self, 'error/error_page.html')
            else:
                if user_id and user_id==users.id:
                    user = User()
                    user.id = user_id
                    user.set_password(self.POST.get('password', ''))
                    user.save()
                    user_file = UserProfile()
                    user_file.user_id = user.id
                    for val in group:
                        user_file.group.remove(val)
                        user_file.group.add(val)

                return render(self, 'error/error_page.html', {'code':0,'msg':u'该用户没有添加用户的权限！'})

    save_user = staff_member_required(save_user)

    @csrf_exempt
    def delete_user(self):
        users = self.user
        if users.is_authenticated():
            user_file = UserProfile.objects.get(user=users.id)
            if user_file.role == 2:
                del_id = self.GET['id']
                if isinstance(del_id, str):
                    del_id = [int(del_id)]
                res = UserProfile.objects.filter(id__in=del_id).update(state=0)
                if res:
                    return render(self, 'error/error_page.html')
            else:
                return render(self, 'error/error_page.html', {'code': 0, 'msg': u'没有删除用户的权限！'})

    @csrf_exempt
    def user_detail(self):
        id = self.GET['id']
        users = self.user
        if users.is_authenticated():
            user_file = UserProfile.objects.get(user=users.id)
            if not user_file.role == 2 and not users.id == id:
                return render(self, 'error/error_page.html', {'code': 0, 'msg': u'没有的权限！'})

            user = User.objects.get(id=id)
            return render(self, 'error/error_page.html', {'code': 1, 'data': user})

    def user_list(self):
        user = App.get_user_info(self)
        if not user or user.role == 0:
            return HttpResponseRedirect("/admin/maxlead_site/index/")
        role_list = ['member', 'Leader', 'Admin']
        user_list = UserProfile.objects.filter(state__gt=0 )
        menber_group = MenberGroups.objects.all()
        role = self.GET.get('role','')
        if role:
            user_list = user_list.filter(role=role)
        group = self.GET.get('group','')
        if group:
            user_list = user_list.filter(group=group)
        status = self.GET.get('status','')
        if status:
            user_list = user_list.filter(state=status)
        keywords = self.GET.get('keywords','')
        if keywords:
            user_list = user_list.filter(Q(username__icontains=keywords) | Q(email__icontains=keywords))

        limit = self.GET.get('limit',1)
        total_count = user_list.count()
        if limit >= total_count:
            limit = total_count
        paginator = Paginator(user_list, limit)
        page = self.GET.get('page')
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            users = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            users = paginator.page(paginator.num_pages)

        for val in users:
            val.group_str = ''
            for i in list(val.group.all()):
                val.group_str+=i.name + " "
            val.role = role_list[val.role]
            val.user.date_joined = val.user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
            if val.user.last_login:
                val.user.last_login = val.user.last_login.strftime("%Y-%m-%d %H:%M:%S")
            else:
                val.user.last_login = ''

        data = {
            'users': users,
            'groups':list(menber_group),
            'total_count':total_count,
            'total_page':int(total_count/limit),
            'user': user,
            'avator': user.user.username[0]
        }

        return render(self, 'user/useradmin.html', data)