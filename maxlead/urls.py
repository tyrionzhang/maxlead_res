"""maxlead URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from maxlead_site.views import views as max_views
from maxlead_site.views.views import test as test_views
from maxlead_site.views.users.login import Logins

urlpatterns = [
    # url(r'^admin/warehouse/spiders/', warehouse_views.home),
    url(r'^admin/maxlead_site/spiders/', max_views.RunReview),
    url(r'^admin/maxlead_site/user_info/', test_views.user_info),
    url(r'^admin/maxlead_site/login/', Logins.userLogin),
    url(r'^admin/maxlead_site/logout/', Logins.logout),
    url(r'^admin/maxlead_site/forget_pass/', Logins.forget_password_for_email),
    url(r'^admin/maxlead_site/reset_pass/', Logins.email_reset_pass),
    url(r'^admin/maxlead_site/save_user/', Logins.save_user),
    url(r'^admin/maxlead_site/delete_user/', Logins.delete_user),
    url(r'^admin/maxlead_site/user_detail/', Logins.user_detail),
    url(r'^admin/', admin.site.urls),

]
