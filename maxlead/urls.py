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
from maxlead_site.views.index.index import Index
from maxlead_site.views.listing.listing import Listing
from maxlead_site.views.listing.item import Item
from maxlead_site.views.dashboard.dashboard import Dashboard
from maxlead_site.views.miner.miner import Miner
from django.views import static
from maxlead import settings

urlpatterns = [
    # url(r'^admin/warehouse/spiders/', warehouse_views.home),
    url(r'^static/(?P<path>.*)$', static.serve,{ 'document_root': settings.STATIC_URL }),
    url(r'^download/(?P<path>.*)$', static.serve,{ 'document_root': settings.DOWNLOAD_URL }),
    url(r'^admin/maxlead_site/spiders/', max_views.RunReview),
    url(r'^admin/maxlead_site/test/', max_views.test1),
    url(r'^admin/maxlead_site/user_info/', test_views.user_info),
    url(r'^admin/maxlead_site/login/', Logins.userLogin),
    url(r'^admin/maxlead_site/logout/', Logins.logout),
    url(r'^admin/maxlead_site/forget_pass/', Logins.forget_password_for_email),
    url(r'^admin/maxlead_site/reset_pass/', Logins.email_reset_pass),
    url(r'^admin/maxlead_site/change_pass/', Logins.change_pass),
    url(r'^admin/maxlead_site/save_user/', Logins.save_user),
    url(r'^admin/maxlead_site/delete_user/', Logins.delete_user),
    url(r'^admin/maxlead_site/user_detail/', Logins.user_detail),
    url(r'^admin/maxlead_site/index/', Index.index),
    url(r'^admin/maxlead_site/user_list/', Logins.user_list),
    url(r'^admin/maxlead_site/listings/', Listing.index),
    url(r'^admin/maxlead_site/add_asin/', Listing.save_user_asin),
    url(r'^admin/maxlead_site/get_asin_edits/', Listing.ajax_get_asins),
    url(r'^admin/maxlead_site/ajax_edit/', Listing.ajax_get_asins1),
    url(r'^admin/maxlead_site/listing_export/', Listing.ajax_export),
    url(r'^admin/maxlead_site/listing_item/', Item.item),
    url(r'^admin/maxlead_site/review_search/', Item.ajax_get_review),
    url(r'^admin/maxlead_site/export_qa/', Item.export_qa),
    url(r'^admin/maxlead_site/export_reviews/', Item.export_reviews),
    url(r'^admin/maxlead_site/shuttle_chart/', Item.ajax_chart),
    url(r'^admin/maxlead_site/export_shuttle/', Item.export_shuttle),
    url(r'^admin/maxlead_site/dashboard/', Dashboard.index),
    url(r'^admin/maxlead_site/miner/', Miner.index),
    url(r'^admin/maxlead_site/ajax_reviews/', Dashboard.ajax_get_reviews),
    url(r'^admin/maxlead_site/expload_dash_reviews/', Dashboard.export_dash_reviews),
    url(r'^admin/maxlead_site/ajax_rising/', Dashboard.ajax_rising),
    url(r'^admin/maxlead_site/export_rising/', Dashboard.export_rising),
    url(r'^admin/maxlead_site/ajax_radar/', Dashboard.ajax_radar),
    url(r'^admin/maxlead_site/export_radar/', Dashboard.export_radar),
    url(r'^admin/', admin.site.urls),

]

