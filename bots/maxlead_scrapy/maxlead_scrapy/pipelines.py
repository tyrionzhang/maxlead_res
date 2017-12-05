# -*- coding: utf-8 -*-

from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.http import Request
import os,json,requests
from bots.maxlead_scrapy.maxlead_scrapy import settings

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# class MyImagesPipeline(ImagesPipeline):
#     def get_media_requests(self, item, info):
#         if 'image_urls' in item and not len(item['image_urls']) == 0:
#             for image_url in item['image_urls']:
#                 yield Request(image_url)
#
#
#     def item_completed(self, results, item, info):
#         image_paths = [x['path'] for ok, x in results if ok]
#         filename = []
#         if not image_paths:
#             raise DropItem("Item contains no images")
#         for img in image_paths:
#             filename.append(os.path.basename(img))
#         item['image_names'] = json.dumps(filename)
#         item.save()
#         return item

class MaxleadScrapyPipeline(object):
    def process_item(self, item, spider):
        if 'image_urls' in item and len(item['image_urls'])>0:  # 如何‘图片地址’在项目中
            images = []  # 定义图片空集

            dir_path = '%s/%s' % (settings.IMAGES_STORE, spider.name)

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            for image_url in item['image_urls']:
                us = image_url.split('/')[3:]
                image_file_name = '_'.join(us)
                file_path = '%s/%s' % (dir_path, image_file_name)
                images.append(file_path)
                if os.path.exists(file_path):
                    continue

                with open(file_path, 'wb') as handle:
                    response = requests.get(image_url, stream=True)
                    for block in response.iter_content(1024):
                        if not block:
                            break

                        handle.write(block)

            item['image_names'] = images
        item.save()
        return item

    def spider_closed(self, spider):
        self.file.close()
