# -*- coding: utf-8 -*-
import time,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from maxlead_site.models import UserProfile
from maxlead import settings
from maxlead_site.common.prpcrypt import Prpcrypt
from maxlead_site.views import commons
from maxlead_site.views.app import App


class Logins:
    role = ['member','Leader','admin']

    @csrf_exempt
    def userLogin(self):
        if self.user.is_authenticated:
            return HttpResponseRedirect("/admin/maxlead_site/index/",{'user': self.user,'avator':self.user.username[0]})
        if self.method == 'POST':
            username = self.POST.get('username', '')
            password = self.POST.get('password', '')
            user = auth.authenticate(username=username, password=password)
            if not user:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'账号/密码错误，请确认后重试！'}), content_type='application/json')
            user1 = User.objects.get(username=username)
            user_file = UserProfile.objects.filter(user=user1.id)
            if user_file[0].state in (0,2):
                return HttpResponse(json.dumps({'code': 0, 'msg': u'账号不存在/已被锁定,请联系管理员！'}), content_type='application/json')

            if user.is_active and user_file[0].state == 1:
                user_file.update(er_count=0,em_count=0)
                auth.login(self, user)
                self.session.set_expiry(604800) # 登陆状态生命
                commons.loger(description='用户登陆正常',user=user,name='用户登陆')
                return HttpResponse(json.dumps({'code': 1, 'msg': u'用户登陆正常!'}),content_type='application/json')
            else:
                if user_file[0].em_count >= 5:
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'密码错误超过5次，账号已被锁定'}),
                                        content_type='application/json')
                er_count = user_file[0].er_count+1
                now_time = int(time.time())
                user_file.update(er_count=er_count,er_time=now_time)
                if er_count>=5 and now_time-user_file[0].er_time<=86400:
                    user_file.update(state=2) #2,账号锁定
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'密码错误超过5次，账号已被锁定'}),
                                        content_type='application/json')

        return render(self,"user/signin.html")

    def logout(self):
        auth.logout(self)
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    @csrf_exempt
    def forget_password_for_email(self):
        username = self.POST.get('username', '')
        email = self.POST.get('email', '')
        user = User.objects.get(username=username,email=email)

        if not user:
            user_file = UserProfile.objects.filter(user=user.id)
            if user_file[0].em_count>=5:
                return HttpResponse(json.dumps({'code':0,'msg':u'连续输入错误邮箱超过5次，账号已被锁定'}),
                                content_type='application/json')
            em_count = user_file[0].em_count + 1
            now_time = int(time.time())
            user_file.update(em_count=em_count, er_time=now_time)
            if em_count >= 5 and now_time - user_file[0].er_time <= 86400:
                user_file.update(state=2)  # 2,
                return HttpResponse(json.dumps({'code': 0, 'msg': u'连续输入错误邮箱超过5次，账号已被锁定'}),
                                    content_type='application/json')
            return HttpResponse(json.dumps({'code': 0, 'msg': u'邮箱有误'}),
                                content_type='application/json')

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
        return HttpResponse(json.dumps({'code': 1, 'msg': u'提交成功，请尽快完成密码重置'}),
                            content_type='application/json')

    def email_reset_pass(self):
        key_words = self.GET['key_words']
        did = self.GET['did']
        if key_words and did:
            key_words = Prpcrypt.decrypt(self,key_words)
            did = Prpcrypt.decrypt(self,did)
            now_time = int(time.time())
            # if now_time - int(did) < 180 and key_words:
            if key_words:
                username = key_words.split('||')[0]
                email = key_words.split('||')[1]
                user_info = UserProfile.objects.get(user__username=username,user__email=email)
                user = user_info
                user.role=99
                return render(self, 'user/reset_pass.html',
                              {'user': user, 'avator': user.user.username[0], 'user_info': user_info,'key_words':key_words,'did':did})
            else:
                return render(self, 'error/login_page.html', {'msg': 'url地址已过期/参数有误！'})
        else:
            return render(self, 'error/login_page.html', {'msg': 'url地址参数有误！'})

    @csrf_exempt
    def change_pass(self):
        key_words = self.POST.get('key_words','')
        did = self.POST.get('did','')
        username = self.POST.get('username','')
        email = self.POST.get('email','')
        password = self.POST.get('password','')

        now_time = int(time.time())
        if now_time - int(did) < 180 and key_words:
            user_info = User.objects.filter(username=username, email=email)
            users = User()
            users.set_password(password)
            re = user_info.update(password=users.password)
            if not re:
                return render(self, 'error/login_page.html', {'msg': '修改失败！'})
            return HttpResponseRedirect("/admin/maxlead_site/login/", {'msg': '修改成功！'})


    @csrf_exempt
    def save_user(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        if self.method == 'POST':
            user_id = self.POST.get('id', '')
            group = self.POST.get('group', 1)

            user_file = user

            update_fields = ['username', 'email']
            update_fields1 = ['state', 'role', 'group']
            if user_file.role == 2:
                user = User()
                user.username = self.POST.get('username', '')
                if self.POST.get('password', ''):
                    user.set_password(self.POST.get('password', ''))
                    update_fields.append('password')
                user.email = self.POST.get('email', '')
                if user_id:
                    user_pro = UserProfile.objects.get(id=user_id)
                    user.id = user_pro.user.id
                    user.save(update_fields=update_fields)
                else:
                    user.id
                    user.save()

                user_file = UserProfile()
                user_file.id = user.userprofile.id
                user_file.user_id = user.id
                user_file.state = self.POST.get('state', '')
                user_file.role = self.POST.get('role', '')
                if user_file.role == '1':
                    group = user_file.id
                if not group:
                    group = 1
                user_file.group = UserProfile.objects.filter(id=int(group))[0]

                user_file.save(update_fields=update_fields1)

                return HttpResponseRedirect("/admin/maxlead_site/user_list/")
            else:
                if user_id and int(user_id)==user.id:
                    user = User()
                    user.id = user_file.user.id
                    user.username = self.POST.get('username', '')
                    user.email = self.POST.get('email', '')
                    if self.POST.get('password', ''):
                        user.set_password(self.POST.get('password', ''))
                        update_fields.append('password')
                    user.save(update_fields=update_fields)
                    user_file = UserProfile()
                    user_file.id = user.id

                return HttpResponseRedirect("/admin/maxlead_site/user_detail/")
        else:
            if user.role == 2:
                menber_group = UserProfile.objects.filter(role=1,state=1).all()
                return render(self, 'user/add.html', {'user': user,'avator': user.user.username[0],'member_groups':menber_group})
            else:
                return HttpResponseRedirect("/admin/maxlead_site/index/")


    @csrf_exempt
    def delete_user(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 2, 'msg': u'没有登陆！'}), content_type='application/json')
        if not user.role == 2:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'没有的权限！'}), content_type='application/json')

        del_id = eval(self.POST['ids'])
        res = UserProfile.objects.filter(id__in=del_id).exclude(id=user.id).update(state=0)
        if res:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'删除成功！'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'删除失败！'}), content_type='application/json')

    @csrf_exempt
    def user_detail(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        id = self.GET.get('id')
        member_group = list(UserProfile.objects.filter(role=1,state=1))

        if not id:
            user_info = user
            return render(self, 'user/userinfo.html', {'user': user,'avator': user.user.username[0],'user_info': user_info,'member_groups':member_group,})

        if not user.role == 2:
            return HttpResponseRedirect("/admin/maxlead_site/index/")

        user_info = UserProfile.objects.get(id=id)
        return render(self, 'user/userinfo.html', {'user': user,'avator': user.user.username[0],'user_info': user_info,'member_groups':member_group,})

    def user_list(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        if user.role == 0:
            return HttpResponseRedirect("/admin/maxlead_site/index/")
        role_list = ['member', 'Leader', 'Admin']
        user_list = UserProfile.objects.filter(state__gt=0 )
        if user.role == 1:
            user_list = user_list.filter(group=user.user)

        member_group = UserProfile.objects.filter(role=1,state=1).all()
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
            user_list = user_list.filter(Q(user__username__icontains=keywords) | Q(user__email__icontains=keywords))

        limit = self.GET.get('limit',20)
        total_count = user_list.count()
        if int(limit) >= total_count:
            limit = total_count
        if not user_list:
            return render(self, 'user/useradmin.html', {'data':''})
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
            val.role = role_list[val.role]
            val.user.date_joined = val.user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
            if val.user.last_login:
                val.user.last_login = val.user.last_login.strftime("%Y-%m-%d %H:%M:%S")
            else:
                val.user.last_login = ''
        urls = self.get_raw_uri()
        urls_li = urls.split('page=')
        if len(urls_li) >= 2:
            urls = urls_li[0]+urls_li[1][2:]
        if '?' not in urls:
            urls = urls+'?'
        urls = urls.replace('&amp;',' ')
        data = {
            'data':True,
            'users': users,
            'groups':list(member_group),
            'total_count':total_count,
            'total_page':int(total_count/limit),
            'user': user,
            'avator': user.user.username[0],
            'urls': urls,
            'page': page,
            'role': role,
            'group': int(group),
            'keywords': keywords,
            'state': status,
        }

        return render(self, 'user/useradmin.html', data)