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

# views of max_stock
from max_stock.views import views as stock_views
from max_stock.views import users as stock_users
from max_stock.views import users_sku as skus
from max_stock.views import stocks
from max_stock.views import auto_email
from max_stock.views import setting
from max_stock.views import order_email_temp as emailTmp,order_items
from django.views import static
from maxlead import settings

urlpatterns = [
    # url(r'^admin/warehouse/spider/', warehouse_views.home),
    url(r'^static/(?P<path>.*)$', static.serve,{ 'document_root': settings.STATIC_URL }),
    url(r'^download/(?P<path>.*)$', static.serve,{ 'document_root': settings.DOWNLOAD_URL }),
    url(r'^admin/maxlead_site/spiders2/', max_views.Spiders2),
    url(r'^admin/maxlead_site/spiders1/', max_views.Spiders1),
    url(r'^admin/maxlead_site/test1/', max_views.test_spider),
    url(r'^admin/maxlead_site/run_command_queue/', max_views.run_command_queue),
    url(r'^admin/maxlead_site/back_upTable/', max_views.back_upTable),
    url(r'^admin/maxlead_site/test/', max_views.test1),
    # url(r'^.well-known/acme-challenge/(.+)/$', max_views.letsencrpyt),
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
    url(r'^admin/maxlead_site/add_run_spiders/', Listing.add_run_spiders),
    url(r'^admin/maxlead_site/listing_export/', Listing.ajax_export),
    url(r'^admin/maxlead_site/del_asins/', Listing.del_asins),
    url(r'^admin/maxlead_site/ajax_update_list/', Listing.ajax_update_list),
    url(r'^admin/maxlead_site/listing_item/', Item.item),
    url(r'^admin/maxlead_site/review_search/', Item.ajax_get_review),
    url(r'^admin/maxlead_site/export_qa/', Item.export_qa),
    url(r'^admin/maxlead_site/export_reviews/', Item.export_reviews),
    url(r'^admin/maxlead_site/shuttle_chart/', Item.ajax_chart),
    url(r'^admin/maxlead_site/export_shuttle/', Item.export_shuttle),
    url(r'^admin/maxlead_site/ajax_get_radar/', Item.ajax_get_radar),
    url(r'^admin/maxlead_site/ajax_get_watcher/', Item.ajax_get_watcher),
    url(r'^admin/maxlead_site/item_offers/', Item.item_offers),
    url(r'^admin/maxlead_site/question_answer/', Item.question_answer),
    url(r'^admin/maxlead_site/ajax_k_rank/', Item.ajax_k_rank),
    url(r'^admin/maxlead_site/export_k_rank/', Item.export_k_rank),
    url(r'^admin/maxlead_site/ajax_update_listing/', Item.ajax_update_listing),
    url(r'^admin/maxlead_site/dashboard/', Dashboard.index),
    url(r'^admin/maxlead_site/ajax_watcher/', Dashboard.ajax_watcher),
    url(r'^admin/maxlead_site/export_watcher/', Dashboard.export_watcher),
    url(r'^admin/maxlead_site/miner/', Miner.index),
    url(r'^admin/maxlead_site/ajax_reviews/', Dashboard.ajax_get_reviews),
    url(r'^admin/maxlead_site/expload_dash_reviews/', Dashboard.export_dash_reviews),
    url(r'^admin/maxlead_site/ajax_rising/', Dashboard.ajax_rising),
    url(r'^admin/maxlead_site/export_rising/', Dashboard.export_rising),
    url(r'^admin/maxlead_site/ajax_radar/', Dashboard.ajax_radar),
    url(r'^admin/maxlead_site/export_radar/', Dashboard.export_radar),
    url(r'^admin/maxlead_site/task_add/', Miner.add),
    url(r'^admin/maxlead_site/ajax_get_miner_data/', Miner.ajax_get_miner_data),
    url(r'^admin/maxlead_site/ajax_get_task_data/', Miner.ajax_get_task_data),
    url(r'^admin/maxlead_site/delete_task_data/', Miner.delete_task_data),
    url(r'^admin/$', Dashboard.index),
    url('^$', Dashboard.index),
    url('^admin/maxlead_site/$', Dashboard.index),
    url('^admin/maxlead_site/export_users/', max_views.export_users),

    # urls of max_stock
    url('^admin/max_stock/stock_spiders/', stock_views.stock_spiders),
    url('^admin/max_stock/test/', stock_views.test),
    url('^admin/max_stock/empty_data/', stock_views.empty_data),
    url('^admin/max_stock/login/', stock_users.userLogin),
    url('^admin/max_stock/user_list/', stock_users.user_list),
    url('^admin/max_stock/user_save/', stock_users.user_save),
    url('^admin/max_stock/users_import/', stock_users.users_import),
    url('^admin/max_stock/users_del/', stock_users.users_del),
    url('^admin/max_stock/logout/', stock_users.logout),
    url('^admin/max_stock/index/', stocks.index),
    url('^admin/max_stock/reviews/', stocks.index),
    url('^admin/max_stock/$', stocks.index),
    url('^admin/max_stock/stock_checked/', stocks.stock_checked),
    url('^admin/max_stock/checked_edit/', stocks.checked_edit),
    url('^admin/max_stock/checked_batch_edit/', stocks.checked_batch_edit),
    url('^admin/max_stock/export_stocks/', stocks.export_stocks),
    url('^admin/max_stock/threshold/', stocks.threshold),
    url('^admin/max_stock/threshold_add/', stocks.threshold_add),
    url('^admin/max_stock/get_threshold/', stocks.get_threshold),
    url('^admin/max_stock/threshold_del/', stocks.threshold_del),
    url('^admin/max_stock/threshold_import/', stocks.threshold_import),
    url('^admin/max_stock/check_new/', stocks.check_new),
    url('^admin/max_stock/check_all_new/', stocks.check_all_new),
    url('^admin/max_stock/covered_new/', stocks.covered_new),
    url('^admin/max_stock/covered_new_all/', stocks.covered_new_all),
    url('^admin/max_stock/covered_give_up/', stocks.covered_give_up),
    url('^admin/max_stock/users_sku/', skus.sku_list),
    url('^admin/max_stock/save_sku/', skus.save_sku),
    url('^admin/max_stock/import_sku/', skus.import_sku),
    url('^admin/max_stock/del_sku/', skus.del_sku),
    url('^admin/max_stock/logs/', skus.logs),
    url('^admin/auto_email/code_index/', auto_email.code_index),
    url('^admin/auto_email/code_save/', auto_email.code_save),
    url('^admin/auto_email/orders/', auto_email.orders),
    url('^admin/setting/index/', setting.index),
    url('^admin/setting/update_menus/', setting.update_menus),
    url('^admin/setting/add_role/', setting.add_role),
    url('^admin/setting/change_role/', setting.change_role),
    url('^admin/setting/get_role/', setting.get_role_by_user),
    url('^admin/setting/get_menus/', setting.get_menus_by_role),
    url('^admin/setting/get_role_user/', setting.get_role_user),
    url('^admin/setting/get_save_role_user/', setting.get_save_role_user),
    url('^admin/send_email/email_temps/', emailTmp.email_temps),
    url('^admin/send_email/tmp_save/', emailTmp.tmp_save),
    url('^admin/send_email/del_tmp/', emailTmp.del_tmp),
    url('^admin/send_email/batch_del_tmp/', emailTmp.batch_del_tmp),
    url('^admin/send_email/branch_edit_tmp/', emailTmp.branch_edit_tmp),
    url('^admin/send_email/tmp_import/', emailTmp.tmp_import),
    url('^admin/send_email/order_list/', order_items.order_list),
    url('^admin/send_email/order_list2/', order_items.order_list),
    url('^admin/send_email/order_save/', order_items.order_save),
    url('^admin/send_email/order_import/', order_items.order_import),
    url('^admin/send_email/send_email/', order_items.send_email),
    url('^admin/send_email/no_send_list/', order_items.no_send_list),
    url('^admin/send_email/check_order_import/', order_items.check_order_import),
    url('^admin/send_email/del_check_order/', order_items.del_check_order),
    url('^admin/send_email/orders_del/', order_items.orders_del),
    url('^admin/send_email/contact_list/', order_items.contact_list),
    url('^admin/send_email/update_emails/', order_items.update_emails),
    url('^admin/send_email/batch_del_ocheck/', order_items.batch_del_ocheck),
    url('^admin/send_email/batch_del_contact/', order_items.batch_del_contact),
]

