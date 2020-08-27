# -*- coding: utf-8 -*-
from PIL import Image
import requests
import time,os,string
from scipy import spatial
from maxlead import settings

# 通过url链接获取验证码图片，并写入本地文件夹里
def get_image(path,url):
    """
    :param path: 文件夹路径
    :param url:  验证码url链接
    """
    respon = requests.get(url=url)      # 请求验证码url
    with open(path,"wb") as file:
        file.write(respon.content)      # 将验证码写到本地


def get_x_coord(image):
    image_width = image.size[0]
    image_height = image.size[1]

    crop_list = []
    start_pos = 0
    is_start_one_char = False

    for x in range(image_width):
        is_black_pos = False
        for y in range(image_height):
            pixel = image.getpixel((x,y))
            if pixel == 0:
                if is_start_one_char == False:
                    start_pos = x
                is_black_pos = True
                is_start_one_char = True
                break
        if is_start_one_char== True and is_black_pos == False:
            end_pos = x
            is_start_one_char = False
            crop_list.append((start_pos, end_pos))

    return crop_list

def match_captcha(img_path):
    im = Image.open(img_path)

    im = im.convert('P')

    im_size = im.size

    new_im = Image.new('P', im_size, 255)

    im_width = im_size[0]
    im_height = im_size[1]

    for y in range(im_height):
        for x in range(im_width):
            pixel = im.getpixel((x, y))
            if pixel == 0:
                new_im.putpixel((x, y), pixel)

    crop_list = get_x_coord(new_im)

    match_captcha = []
    for crop in crop_list:
        crop_im = new_im.crop((crop[0], 0, crop[1], im_height))  # （左上x， 左上y， 右下x， 右下y）
        filename = os.path.join(settings.BASE_DIR,"maxlead_site/common/amazon_captcha/letter", str(time.time()) + ".gif")
        crop_im.save(filename)

        all_result = []  # 单个切片的所有字母的相似性

        remove_letter = ['d', 'i', 'o', 'q', 's', 'v', 'w', 'z']
        for letter in list(set(string.ascii_lowercase) - set(remove_letter)):

            refer_image_dir = os.path.join(settings.BASE_DIR,"maxlead_site/common/amazon_captcha/training_library", letter)

            for refer_image in os.listdir(refer_image_dir):
                refer_im = Image.open(os.path.join(refer_image_dir, refer_image))

                crop_list = list(crop_im.getdata())
                refer_list = list(refer_im.getdata())
                min_count = min(len(crop_list), len(refer_list))

                result = 1 - spatial.distance.cosine(crop_list[:min_count - 1], refer_list[:min_count - 1])
                all_result.append({'letter': letter, 'result': result})

        match_letter = max(all_result, key=lambda x: x['result']).get('letter')
        match_captcha.append(match_letter)

    return ''.join(match_captcha)

if __name__ == '__main__':
    img_path = "D:"                                 # 文件夹目录
    img_path = img_path + "\Captcha_amykba.jpg"               # 验证码图片所在的目录及名称

    im = Image.open(img_path)

    im = im.convert('P')

    im_size = im.size

    new_im = Image.new('P', im_size, 255)

    im_width = im_size[0]
    im_height = im_size[1]

    for y in range(im_height):
        for x in range(im_width):
            pixel = im.getpixel((x, y))
            if pixel == 0:
                new_im.putpixel((x, y), pixel)

    crop_list = get_x_coord(new_im)

    match_captcha = []
    for crop in crop_list:
        crop_im = new_im.crop((crop[0], 0, crop[1], im_height))  # （左上x， 左上y， 右下x， 右下y）
        filename = 'letter\\' + str(time.time()) + '.gif'
        crop_im.save(filename)

        all_result = []  # 单个切片的所有字母的相似性

        remove_letter = ['d', 'i', 'o', 'q', 's', 'v', 'w', 'z']
        for letter in list(set(string.ascii_lowercase) - set(remove_letter)):

            refer_image_dir = r'training_library\%s' % letter

            for refer_image in os.listdir(refer_image_dir):
                refer_im = Image.open(os.path.join(refer_image_dir, refer_image))

                crop_list = list(crop_im.getdata())
                refer_list = list(refer_im.getdata())
                min_count = min(len(crop_list), len(refer_list))

                result = 1 - spatial.distance.cosine(crop_list[:min_count - 1], refer_list[:min_count - 1])
                all_result.append({'letter': letter, 'result': result})

        match_letter = max(all_result, key=lambda x: x['result']).get('letter')
        match_captcha.append(match_letter)

    print('验证码为：{0}'.format(''.join(match_captcha)))