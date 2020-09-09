#!/usr/bin/python
#coding=utf-8
#__author__='dahu'
#data=2017-
#
import requests
import time
import random
from pymongo import MongoClient
from bson.objectid import ObjectId
url = 'https://www.amazon.com/'
client = MongoClient('localhost', 27017)
db = client['save_cookie']
collection = db['san60cookie']

user_agent_list = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]

def get_header():
    header={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "www.amazon.com",
        "Upgrade-Insecure-Requests": "1",
    }
    return header

def get_cookie_lib():
    headers = get_header()
    headers['User-Agent'] = random.choice(user_agent_list)
    response = requests.get(url,headers=headers)
    # for item in cookie:
    #     print "%s : %s" % (item.name, item.value)
    cookie_dict = {}
    for cook in response.cookies:
        cookie_dict[cook.name] = cook.value
    return cookie_dict


def save_cookie_into_mongodb(cookie):
    insert_data = {}
    insert_data['cookie'] = cookie
    insert_data['insert_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    insert_data['request_url']=url
    insert_data['insert_timestamp'] = time.time()
    collection.insert(insert_data)


def delete_timeout_cookie(request_url):
    time_out = 300
    for data in collection.find({'request_url':request_url}):
        if (time.time() - data.get('insert_timestamp')) > time_out:
            collection.delete_one({'_id': ObjectId(data.get('_id'))}) #这里有疑问的话可以参考http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid　

def get_cookie_from_mongodb():
    cookies = [data.get('cookie') for data in collection.find()]
    return cookies

if __name__ == '__main__':
    num=0
    while 1:
        if num == 2:
            delete_timeout_cookie(url)
            num = 0
        else:
            cookie = get_cookie_lib()
            save_cookie_into_mongodb(cookie)
            num += 1
            time.sleep(5)