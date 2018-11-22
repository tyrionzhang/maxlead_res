# -*- coding: utf-8 -*-
"""
WSGI config for maxlead project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os,threading
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UserAdmin.settings")
django.setup()
from django.core.wsgi import get_wsgi_application
from maxlead_site.views.views import download_listings,get_send_time,perform_command,perform_command1

p = os.popen('scrapyd')
print(p)
time_re1 = int(get_send_time('04:00'))
time_re2 = time_re1 - 3600
t1 = threading.Timer(float('%.1f' % time_re2), download_listings)
t1.start()

time_re3 = int(get_send_time('23:00'))
time_re4 = time_re3 - 3600
t2 = threading.Timer(float('%.1f' % time_re4), perform_command)
t2.start()
t3 = threading.Timer(float('%.1f' % time_re3), perform_command1)
t3.start()

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxlead.settings")
os.environ['DJANGO_SETTINGS_MODULE'] = 'maxlead.settings'

application = get_wsgi_application()

