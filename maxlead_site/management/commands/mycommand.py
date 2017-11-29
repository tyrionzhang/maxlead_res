#-*-coding:utf-8-*-

from maxlead import settings
import os, json

from django.core.management.base import BaseCommand, CommandError
from polls.models import Poll


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # 必须实现的方法
    def handle(self, *args, **options):
        for poll_id in options['poll_id']:
            try:
                poll = Poll.objects.get(pk=poll_id)
            except Poll.DoesNotExist:
                raise CommandError('Poll "%s" does not exist' % poll_id)

            poll.opened = False
            poll.save()

            self.stdout.write('Successfully closed poll "%s"' % poll_id)

    def run_review(self, *args, **options):
        work_path = settings.SPIDER_URL
        os.chdir(work_path)  # 修改当前工作目录
        os.system('scrapyd')
        output = os.popen('scrapyd-deploy')
        re = json.loads(output.read())
        if re['status'] == 'ok':
            os.popen('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')