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
from max_stock.views.views import run_command_queue,task_save_stocks

t = threading.Timer(1.0, spiders2)
t.start()

time_re5 = int(get_send_time('08:00'))
# time_re6 = time_re5 + 1800
t4 = threading.Timer(float('%.1f' % time_re5), run_command_queue)
t4.start()
# t5 = threading.Timer(float('%.1f' % time_re6), task_save_stocks)
# t5.start()

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

