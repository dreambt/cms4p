# -*- coding: utf-8 -*-
import json
import time

from common import BaseHandler, pagecache, getAttr

from model import Category


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
        try:
            timestamp = int(time.time())
            post_dic = {
                'email': self.get_argument("email"),
                'add_time': timestamp,
            }
            self.write(json.dumps("error"))
        except:
            self.write(json.dumps("error"))

        return


class Robots(BaseHandler):
    def get(self):
        self.echo('robots.txt', {'cats': Category.get_by_id()})


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
