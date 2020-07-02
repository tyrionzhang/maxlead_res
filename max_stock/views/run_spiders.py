import os
import threading
from rest_framework.response import Response
from rest_framework.decorators import api_view
from maxlead import settings
from bots.stocks.stocks import settings as bot_settings

@api_view(['POST'])
def RunSpiders(request, format=None):
    import pymysql
    from sshtunnel import SSHTunnelForwarder
    # if 'HTTP_AUTHORIZATION' in request.META:
    #     auth_re = request.META.get('HTTP_AUTHORIZATION').split()
    #     if len(auth_re) != 2 or auth_re[0].lower() != "basic":
    #         return Response({'status': 400, 'msg': '授权错误'})
    # else:
    #     return Response({'status': 400, 'msg': '授权错误'})
    warehouse = request.POST.get('warehouse')
    if not warehouse:
        return Response({'status': 200, 'msg': '请选择仓库'})
    warehouse = warehouse.split('|')
    server = SSHTunnelForwarder(
        (bot_settings.SSH_HOST, bot_settings.SSH_PORT),  # B机器的配置
        ssh_password=bot_settings.SSH_PASSWORD,
        ssh_username=bot_settings.SSH_USER,
        remote_bind_address=(bot_settings.MYSQL_HOST, bot_settings.MYSQL_PORT),
        local_bind_address=('127.0.0.1', bot_settings.MYSQL_PORT))  # A机器的配置
    server.start()
    conn = pymysql.connect(host='127.0.0.1',  # 此处必须是是127.0.0.1
                            port=server.local_bind_port,
                            user=bot_settings.MYSQL_USER,
                            password=bot_settings.MYSQL_PASSWORD,
                            db=bot_settings.MYSQL_DB_NAME,
                            charset='utf8',
                            cursorclass=pymysql.cursors.DictCursor)
    db_cur = conn.cursor()
    spiders = []
    try:
        if 'ZTO' in warehouse:
            check_sql = "select id from mmc_spider_status where warehouse='ZTO' and status=1"
            db_cur.execute(check_sql)
            status = db_cur.fetchone()
            if not status:
                spiders.append({
                    'cmd_str': 'curl http://localhost:6800/schedule.json -d project=stocks -d spider=zto_spider',
                    'time_re': 130
                })
        if 'ATL' in warehouse:
            check_sql = "select id from mmc_spider_status where warehouse='ATL1' and status=1"
            db_cur.execute(check_sql)
            status = db_cur.fetchone()
            if not status:
                spiders.append({
                    'cmd_str': 'curl http://localhost:6800/schedule.json -d project=stocks -d spider=atl1_spider',
                    'time_re': 33
                })
        if 'Hanover' in warehouse:
            check_sql = "select id from mmc_spider_status where warehouse='Hanover' and status=1"
            db_cur.execute(check_sql)
            status = db_cur.fetchone()
            if not status:
                spiders.append({
                    'cmd_str': 'curl http://localhost:6800/schedule.json -d project=stocks -d spider=hanover_spider',
                    'time_re': 170
                })
        if 'TWU' in warehouse:
            check_sql = "select id from mmc_spider_status where warehouse='TWU' and status=1"
            db_cur.execute(check_sql)
            status = db_cur.fetchone()
            if not status:
                spiders.append({
                    'cmd_str': 'curl http://localhost:6800/schedule.json -d project=stocks -d spider=twu_spider',
                    'time_re': 120
                })
        if '3pl' in warehouse:
            check_sql = "select id from mmc_spider_status where warehouse='3pl' and status=1"
            db_cur.execute(check_sql)
            status = db_cur.fetchone()
            if not status:
                spiders.append({
                    'cmd_str': 'curl http://localhost:6800/schedule.json -d project=stocks -d spider=exl_spider',
                    'time_re': 780
                })
        db_cur.close()
        conn.close()
        server.close()
        work_path = settings.MMC_SPIDER_URL
        if spiders:
            os.chdir(work_path)
            os.popen('scrapyd-deploy')
            time_re = 1.0
            for val in spiders:
                t = threading.Timer(time_re, run_spider_by_str, [val['cmd_str']])
                t.start()
                time_re += val['time_re']
        os.chdir(settings.ROOT_PATH)
        os.popen('killall -9 firefox')
        return Response({'status': 200, 'msg': '正在运行中'})
    except Exception as e:
        db_cur.close()
        conn.close()
        server.close()
        return Response({'status': 401, 'msg': '内部错误'})

def run_spider_by_str(cmd_str):
    os.popen(cmd_str)