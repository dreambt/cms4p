#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

_author__ = 'baitao.ji'

import tornado.ioloop
import tornado.web
import os

from controller.admin import urls as adminurls
from controller.blog import urls as blogurls

urls = adminurls + blogurls

settings = {
    'debug': False,
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'cookie_secret': '7nVA0WeZSJSzTCUF8UZB/C3OfLrl7k26iHxfnVa9x0I=',
    'login_url': "/login",
    #"xsrf_cookies": True,
    'gzip': True,
}

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'

application = tornado.web.Application(urls, **settings)

if __name__ == "__main__":
    print "启动中..."
    port = int(sys.argv[1].split('=')[1])
    if not port:
        port = 8080
    application.listen(port)
    print "启动完毕！"
    tornado.ioloop.IOLoop.instance().start()