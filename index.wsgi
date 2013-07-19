import os
import sys

root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root, 'site-packages'))

import sae
import tornado.wsgi

from controller.blog import urls as blogurls
from controller.admin import urls as adminurls

saeurls = blogurls + adminurls

settings = {
    'debug': True,
    #"static_path": os.path.join(os.path.dirname(__file__), "static"),
    'cookie_secret': '7nVA0WeZSJSzTCUF8UZB/C3OfLrl7k26iHxfnVa9x0I=',
    'login_url': "/login",
    #"xsrf_cookies": True,
    #'gzip': True,
}

app = tornado.wsgi.WSGIApplication(saeurls, **settings)

application = sae.create_wsgi_app(app)
