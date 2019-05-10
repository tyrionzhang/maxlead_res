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
from maxlead_site.views.views import download_listings,get_send_time,spiders2,proxy_spiders2
from max_stock.views.views import run_command_queue,task_save_stocks,copy_stocks_of_pc
from max_stock.views.tracking_orders import get_tracking_order_status

os.popen('scrapyd')

time_re5 = int(get_send_time('08:00'))
t4 = threading.Timer(float('%.1f' % time_re5), run_command_queue)
t4.start()

t4_pc = threading.Timer(float('%.1f' % time_re5), copy_stocks_of_pc)
t4_pc.start()

t2 = threading.Timer(1.0, proxy_spiders2)
t2.start()

t = threading.Timer(79200.0, spiders2)
t.start()

time_tr_re = int(get_send_time('15:00'))
t_tr = threading.Timer(1.0, get_tracking_order_status)
t_tr.start()

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

