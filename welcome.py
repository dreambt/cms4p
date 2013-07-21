# -*- coding: utf-8 -*-
import json
import re
import time

from core.common import BaseHandler, pagecache, getAttr
from model import mdb


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
        from model.categories import Categories
        self.echo('robots.txt', {'cats': Categories.get()})


class Sitemap(BaseHandler):
    def get(self, id=''):
        self.set_header('Content-Type', 'text/xml')
        from model.categories import Categories
        self.echo('sitemap.html', {'sitemapstr': Categories.get_sitemap_by_category_id(id), 'id': id})


########
urls = [
    (r"/", HomePage),
    (r"/robots.txt", Robots),
    (r"/sitemap_(\d+)\.xml$", Sitemap),
    (r"/subscribe$", Subscribe),
]