#! /usr/bin/env python
#coding=utf-8
"""
    imageProcess.py
    ~~~~~~~~~~~~~
    Recaptcha and Thumbnail

    :copyright: (c) 2010 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import os
import random
import StringIO

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageEnhance

root_path = os.path.dirname(__file__)


def Recaptcha(text):
    img_width = 100
    img_height = 30
    font_size = 25
    font_style = os.path.join('font', random.choice(
        ['AGENTRED.TTF', 'CRUSOGP.TTF', 'FacesAndCaps.ttf', 'KINKEE.TTF', 'VITAMINOUTLINE.TTF']))
    font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), font_style), font_size)
    #background = (random.randrange(230, 255), random.randrange(230, 255), random.randrange(230, 255))
    colors = [
        (random.randrange(0, 127), random.randrange(0, 127), random.randrange(128, 255)),
        (random.randrange(0, 127), random.randrange(128, 255), random.randrange(0, 127)),
        (random.randrange(128, 255), random.randrange(0, 127), random.randrange(0, 127)),
        # (255, 116, 0),
        # (255, 0, 132),
        # (250, 125, 30),
        # (210, 30, 90),
        # (205, 235, 139),
        # (195, 217, 255),
        # (95, 0, 16),
        # (64, 150, 238),
        # (64, 25, 90),
        # (15, 65, 150),
        # (10, 120, 40),
    ]

    img = Image.new('RGB', size=(img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 画随机干扰线,字数越少,干扰线越多
    c = int(8 / len(text) * 5) or 5
    for i in range(random.randrange(c - 2, c)):
        line_color = (random.randrange(180, 255), random.randrange(180, 255), random.randrange(180, 255))
        xy = (
            random.randrange(0, int(img_width * 0.2)),
            random.randrange(0, img_height),
            random.randrange(3 * img_width / 4, img_width),
            random.randrange(0, img_height)
        )
        draw.line(xy, fill=line_color, width=int(font_size * 0.01))
        #draw.arc(xy, fill=line_color, width=int(font_size * 0.1))
        draw.arc(xy, 0, 5400, fill=line_color)

    # write text
    for i, s in enumerate(text):
        position = (i * 25 + 4, random.randint(0, 6))
        draw.text(position, s, fill=random.choice(colors), font=font)

    # 干扰点
    for w in xrange(img_width):
        for h in xrange(img_height):
            tmp = random.randint(0, 93) / 3
            if tmp > img_height:
                draw.point((w, h), fill=(0, 0, 0))

    # set border
    #draw.line([(0, 0), (99, 0), (99, 29), (0, 29), (0, 0)], fill=(180, 180, 180))
    del draw

    # push data
    strIO = StringIO.StringIO()
    #img.save(strIO, 'JPEG', quality=95)
    img.save(strIO, 'PNG')
    strIO.seek(0)
    return strIO


def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert 0 <= opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


class Thumbnail(object):
    """
        t = Thumbnail(path)
        t.thumb(size=(100,100),outfile='file/to/name.xx',bg=False,watermark=None)
    """

    def __init__(self, path):
        self.path = path
        try:
            self.img = Image.open(self.path)
        except IOError:
            self.img = None
            print "%s not images" % path

    def thumb(self, size=(100, 100), outfile=None, bg=False, watermark=None):
        """
            outfile: 'file/to/outfile.xxx'  
            crop: True|False
            watermark: 'file/to/watermark.xxx'
        """
        if not self.img:
            print 'must be have a image to process'
            return

        # 原图复制
        part = self.img
        part.thumbnail(size, Image.ANTIALIAS)  # 按比例缩略

        size = size if bg else part.size  # 如果没有白底则正常缩放
        w, h = size

        layer = Image.new('RGBA', size, (255, 255, 255))  # 白色底图

        # 计算粘贴的位置
        pw, ph = part.size
        left = (h - ph) / 2
        upper = (w - pw) / 2
        layer.paste(part, (upper, left))  # 粘贴原图

        # 如果有watermark参数则加水印
        if watermark:
            logo = Image.open(watermark)
            logo = reduce_opacity(logo, 0.3)
            # 粘贴到右下角
            lw, lh = logo.size
            position = (w - lw, h - lh)
            if layer.mode != 'RGBA':
                layer.convert('RGBA')
            mark = Image.new('RGBA', layer.size, (0, 0, 0, 0))
            mark.paste(logo, position)
            layer = Image.composite(mark, layer, mark)

        if not outfile:
            outfile = StringIO.StringIO()
            layer.save(outfile, quality=100)
            outfile.seek(0)
        else:
            layer.save(outfile, quality=100)

        return outfile

    def get_font(self, fontname, fontsize):
        return ImageFont.truetype(os.path.join(root_path, fontname), fontsize)

    def thumb_taoke(self, price, commission, outfile=None):
        """
            pic add price and commission
        """
        if not self.img:
            print 'must be have a image to process'
            return

        if not outfile:
            outfile = self.path

        #原图复制
        #layer = Image.new('RGBA', self.img.size, (255,255,255))
        layer = self.img
        w, h = self.img.size
        if layer.mode != 'RGBA':
            layer.convert('RGBA')

        # 创建字体
        price = u'%s' % price
        commission = u"%s" % commission
        unit = u"¥"
        label = u"返利"

        # 创建背景
        price_bg = Image.open(os.path.join(root_path, 'price_bg_big.png'))
        price_bg = reduce_opacity(price_bg, 0.8)
        p_w, p_h = price_bg.size

        comm_bg = Image.open(os.path.join(root_path, 'price_bg_small.png'))
        comm_bg = reduce_opacity(comm_bg, 0.7)
        c_w, c_h = comm_bg.size

        price_left = w - p_w - 10
        price_upper = h / 2 + 10
        comm_left = w - c_w - 10
        comm_upper = price_upper + p_h + 10

        # 粘贴
        mark = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        mark.paste(price_bg, (price_left, price_upper))
        mark.paste(comm_bg, (comm_left, comm_upper))
        layer = Image.composite(mark, layer, mark)

        # 写价格
        font_u_b = self.get_font('AndaleMono.ttf', 22)
        font_u_s = self.get_font('AndaleMono.ttf', 15)
        font_zh = self.get_font('yahei_mono.ttf', 12)

        draw = ImageDraw.Draw(layer)

        # ¥
        draw.text((price_left + 10, price_upper + 4), unit, (255, 255, 255), font=font_u_b)

        # price
        space = 72
        fs = 22
        while True:
            font_temp = self.get_font('AndaleMono.ttf', fs)
            ft_w, ft_h = font_temp.getsize(price)
            if ft_w < space:
                break
            fs -= 1
        position = (price_left + 22 + (space - ft_w) / 2, price_upper + (p_h - ft_h) / 2)
        draw.text(position, price, (255, 255, 255), font=font_temp)

        # 返利
        draw.text((comm_left + 8, comm_upper + 4), label, (255, 224, 0), font=font_zh)

        # ¥
        draw.text((comm_left + 38, comm_upper + 4), unit, (255, 224, 0), font=font_u_s)

        # commission
        space = 48
        fs = 15
        while True:
            font_temp = self.get_font('AndaleMono.ttf', fs)
            ft_w, ft_h = font_temp.getsize(commission)
            if ft_w < space:
                break
            fs -= 1
        position = (comm_left + 45 + (space - ft_w) / 2, comm_upper + (c_h - ft_h) / 2)
        draw.text(position, commission, (255, 224, 0), font=font_temp)

        del draw
        layer.save(outfile, quality=100)
        return outfile


if __name__ == '__main__':
    t = Thumbnail('pic.jpg')
    t.thumb_taoke(219.6, 18.6, 'pic1.jpg')