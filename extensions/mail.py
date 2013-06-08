# -*- coding: utf-8 -*-
import cStringIO
import gzip
import requests
from setting import MAIL_TO, getAttr

_author__ = 'baitao.ji'


# 发送邮件
def sendEmail(subject, html, to=None):
    url = "https://sendcloud.sohu.com/webapi/mail.send.xml"
    if to is None:
        to = MAIL_TO
    params = {
        "api_user": getAttr('MAIL_FROM'),
        "api_key": getAttr('MAIL_KEY'),
        "to": to,
        "from": getAttr('MAIL_FROM'),
        "formname": getAttr('SITE_TITLE'),
        "subject": subject,
        "html": html
    }
    r = requests.post(url, params)
    print r.text


# 邮件 html 压缩
def gzip_compress(content):
    out = cStringIO.StringIO()
    gzipfile = gzip.GzipFile(fileobj=out, mode='w', compresslevel=9)
    gzipfile.write(content)
    gzipfile.close()
    out.seek(0)
    byte = out.read(1)
    byteArr = []
    while byte:
        byteArr.append(byte)
        byte = out.read(1)
    return bytearray(byteArr).decode('iso-8859-1')