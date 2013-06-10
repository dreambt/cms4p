# -*- coding: utf-8 -*-
import json
import re
import time
from tornado import database

from common import BaseHandler, pagecache, getAttr

from model import Category
from setting import *

##数据库配置信息
if debug:
    #已经在setting里设置了
    pass
else:
    import sae.const

    MYSQL_DB = sae.const.MYSQL_DB
    MYSQL_USER = sae.const.MYSQL_USER
    MYSQL_PASS = sae.const.MYSQL_PASS
    MYSQL_HOST_M = sae.const.MYSQL_HOST
    MYSQL_HOST_S = sae.const.MYSQL_HOST_S
    MYSQL_PORT = sae.const.MYSQL_PORT


mdb = database.Connection("%s:%s" % (MYSQL_HOST_M, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=10)
sdb = database.Connection("%s:%s" % (MYSQL_HOST_S, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=10)


class HomePage(BaseHandler):
    @pagecache()
    def get(self):
        output = self.render('index.html', {
            'title': "%s - %s" % (getAttr('SITE_TITLE'), getAttr('SITE_SUB_TITLE')),
            'keywords': getAttr('KEYWORDS'),
            'description': getAttr('SITE_DECR'),
        }, layout='_layout.html')
        self.write(output)
        return output


class Subscribe(BaseHandler):
    def post(self):
        self.set_header("Content-Type", "application/json")
        rspd = {'error': ''}

        email = self.get_argument("email")
        if email:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email):
                try:
                    query = "INSERT INTO `uc_subscribe` (`email`,`add_time`) values(%s,%s)"
                    mdb._ensure_connected()
                    mdb.execute(query, email, int(time.time()))
                    rspd['status'] = 200
                except:
                    rspd['error'] = 'already_subscribed'
            else:
                rspd['error'] = 'invalid_email'
        else:
            rspd['error'] = 'empty_email'

        self.write(json.dumps(rspd))
        return


class Robots(BaseHandler):
    def get(self):
        self.echo('robots.txt', {'cats': Category.get_category()})


class Sitemap(BaseHandler):
    def get(self, id=''):
        self.set_header('Content-Type', 'text/xml')
        self.echo('sitemap.html', {'sitemapstr': Category.get_sitemap_by_id(id), 'id': id})


########
urls = [
    (r"/", HomePage),
    (r"/robots.txt", Robots),
    (r"/sitemap_(\d+)\.xml$", Sitemap),
    (r"/subscribe$", Subscribe),
]
