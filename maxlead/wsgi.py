# -*- coding: utf-8 -*-
"""
WSGI config for maxlead project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os,threading
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'
django.setup()
from django.core.wsgi import get_wsgi_application
from maxlead_site.views.views import download_listings,get_send_time,spiders2
from max_stock.views.views import run_command_queue,task_save_stocks,copy_stocks_of_pc,kill_postgres_on_type,del_orders
from max_stock.views.tracking_orders import get_tracking_order_status
from maxlead import settings

os.popen('scrapyd')

time_re5 = int(get_send_time('07:00'))
t4 = threading.Timer(float('%.1f' % time_re5), run_command_queue)
t4.start()

time_re_pc = int(get_send_time('05:00'))
t4_pc = threading.Timer(float('%.1f' % time_re_pc), copy_stocks_of_pc)
t4_pc.start()

t = threading.Timer(79200.0, spiders2)
t.start()

time_tr_re = int(get_send_time('15:10'))
t_tr = threading.Timer(float('%.1f' % time_tr_re), get_tracking_order_status)
t_tr.start()

time_t_kil_re = int(get_send_time('09:00'))
t_kil_pid = threading.Timer(float('%.1f' % time_tr_re), kill_postgres_on_type)
t_kil_pid.start()

time_del_ord_re = int(get_send_time('01:00'))
t_del_ord_pid = threading.Timer(float('%.1f' % time_del_ord_re), del_orders)
t_del_ord_pid.start()

# os.chdir(settings.PROXY_URL)
# os.popen('python main.py')
# os.chdir(settings.ROOT_PATH)
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

