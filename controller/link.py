# -*- coding: utf-8 -*-
import math

from core.common import BaseHandler, authorized, clear_cache_by_pathlist, getAttr
from model.links import Links

try:
    import json
except:
    import simplejson as json


class LinkController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        link_id = self.get_argument("id", '')

        obj = None
        if act == 'del':
            if link_id:
                Links.delete(link_id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'edit':
            if link_id:
                obj = Links.get(link_id)
                clear_cache_by_pathlist(['/'])

        # 友情链接列表
        page = self.get_argument("page", 1)
        links = Links.get_paged(page, getAttr('ADMIN_LINK_NUM'))
        total = math.ceil(Links.count_all() / float(getAttr('ADMIN_LINK_NUM')))
        if page == 1:
            self.echo('admin_link.html', {
                'title': "友情链接",
                'objs': links,
                'obj': obj,
                'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
                'list': links,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return

    @authorized()
    def post(self):
        try:
            act = self.get_argument("act", '').encode('utf-8')
            link_id = self.get_argument("id", '').encode('utf-8')
            link_name = self.get_argument("name", '').encode('utf-8')
            url = self.get_argument("url", '').encode('utf-8')
            display_order = self.get_argument("sort", '0').encode('utf-8')
        except:
            self.write(json.dumps("网站名称、URL均为必填项！"))
            return

        if link_name and url:
            params = {'link_id': link_id, 'link_name': link_name, 'url': url, 'display_order': display_order}
            if act == 'add':
                Links.create(params)

            if act == 'edit':
                Links.update(params)

            clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))


#####
urls = [
    # 友情链接
    (r"/admin/links", LinkController),
]