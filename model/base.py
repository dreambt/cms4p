# -*- coding: utf-8 -*-
import re

from tornado import database

from core.common import safe_encode
from setting import *


##
HTML_REG = re.compile(r"""<[^>]+>""", re.I | re.M | re.S)
CODE_RE = re.compile(r"""\[code\](.+?)\[/code\]""", re.I | re.M | re.S)

#主数据库 进行Create,Update,Delete 操作
mdb = database.Connection("%s:%s" % (MYSQL_HOST_M, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=MAX_IDLE_TIME)
#从数据库 读取
sdb = database.Connection("%s:%s" % (MYSQL_HOST_S, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=MAX_IDLE_TIME)


def n2br(text):
    con = text.replace('>\n\n', '>').replace('>\n', '>')
    con = "<p>%s</p>" % ('</p><p>'.join(con.split('\n\n')))
    return '<br/>'.join(con.split("\n"))


def tran_content(text, code=False):
    if code:
        codetag = '[mycodeplace]'
        codes = CODE_RE.findall(text)
        for i in range(len(codes)):
            text = text.replace(codes[i], codetag)
        text = text.replace("[code]", "").replace("[/code]", "")

        text = n2br(text)

        a = text.split(codetag)
        b = []
        for i in range(len(a)):
            b.append(a[i])
            try:
                b.append('<pre><code>' + safe_encode(codes[i]) + '</code></pre>')
            except:
                pass

        return ''.join(b)
    else:
        return n2br(text)