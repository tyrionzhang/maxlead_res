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
from maxlead_site.views.views import get_send_time,spiders2
from max_stock.views.views import run_command_queue,task_save_stocks,copy_stocks_of_pc,del_orders,del_logs
from max_stock.views.tracking_orders import get_tracking_order_status
from max_stock.views.barcode import auto_update_barcode
from maxlead_site.common.common import restart_postgres

os.popen('scrapyd')

time_re5 = int(get_send_time('08:10'))
time_re51 = int(get_send_time('22:00'))
t4 = threading.Timer(float('%.1f' % time_re5), run_command_queue)
t41 = threading.Timer(float('%.1f' % time_re51), run_command_queue)
t4.start()
t41.start()

time_re_pc = int(get_send_time('08:50'))
t4_pc = threading.Timer(float('%.1f' % time_re_pc), copy_stocks_of_pc)
t4_pc.start()

# t_re = int(get_send_time('22:45'))
# t = threading.Timer(float('%.1f' % t_re), spiders2)
# t.start()

time_tr_re = int(get_send_time('16:00'))
t_tr = threading.Timer(float('%.1f' % time_tr_re), get_tracking_order_status)
t_tr.start()

time_del_ord_re = int(get_send_time('01:00')) + 432000
t_del_ord_pid = threading.Timer(float('%.1f' % time_del_ord_re), del_orders)
t_del_ord_pid.start()

time_del_log_re = int(get_send_time('02:00')) + 604800
t_del_log_pid = threading.Timer(float('%.1f' % time_del_log_re), del_logs)
t_del_log_pid.start()

t_restart_postgres = threading.Timer(300.0, restart_postgres)
t_restart_postgres.start()

# t_barcode = threading.Timer(21600.0, auto_update_barcode)
# t_barcode.start()

# os.chdir(settings.PROXY_URL)
# os.popen('python main.py')
# os.chdir(settings.ROOT_PATH)
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

