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
from max_stock.views.views import run_command_queue,task_save_stocks

os.popen('scrapyd')

time_re5 = int(get_send_time('08:00'))
time_re2 = int(get_send_time('07:30'))
t4 = threading.Timer(float('%.1f' % time_re5), run_command_queue)
t4.start()

t2 = threading.Timer(float('%.1f' % time_re2), proxy_spiders2)
t2.start()

t = threading.Timer(79200.0, spiders2)
t.start()

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

