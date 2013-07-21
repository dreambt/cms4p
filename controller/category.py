# -*- coding: utf-8 -*-
import math
from core import dthandler

from core.common import BaseHandler, authorized, clear_cache_by_pathlist, getAttr
from model.categories import Categories
from model.showtypes import ShowTypes

try:
    import json
except:
    import simplejson as json


class CategoryController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '').encode('utf-8')
        category_id = self.get_argument("id", '').encode('utf-8')

        obj = None
        if act == 'del':
            if category_id:
                Categories.delete(category_id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'edit':
            if category_id:
                obj = Categories.get(category_id)

        # 分类列表
        page = self.get_argument("page", 1)
        category = Categories.get_paged(page, getAttr('ADMIN_CATEGORY_NUM'))
        total = math.ceil(Categories.count_all() / float(getAttr('ADMIN_CATEGORY_NUM')))
        if page == 1:
            self.echo('admin_category.html', {
                'title': "分类列表",
                'objs': category,
                'obj': obj,
                'category_kv': Categories.get_all_kv(),
                'show_types': ShowTypes.get_all(),
                'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
                'list': category,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result, default=dthandler))
            return

    @authorized()
    def post(self):
        try:
            tf = {'true': 1, 'false': 0}
            act = self.get_argument("act", '').encode('utf-8')
            category_id = self.get_argument("id", '').encode('utf-8')
            father_category_id = self.get_argument("father_id", 0).encode('utf-8')
            category_name = self.get_argument("name", '').encode('utf-8')
            show_type = self.get_argument("show_type", '').encode('utf-8')
            display_order = self.get_argument("sort", '0').encode('utf-8')
            allow_comment = tf[self.get_argument("allow_comment", "true").encode('utf-8')]
            allow_publish = tf[self.get_argument("allow_publish", "true").encode('utf-8')]
            description = self.get_argument("description", '').encode('utf-8')
        except:
            self.write(json.dumps("用户名、密码、验证码均为必填项！"))
            return

        if category_name:
            params = {'category_id': category_id, 'father_category_id': father_category_id,
                      'category_name': category_name, 'show_type': show_type, 'display_order': display_order,
                      'allow_comment': allow_comment, 'allow_publish': allow_publish, 'description': description}
            if act == 'add':
                Categories.create(params)

            if act == 'edit':
                Categories.update(params)

            clear_cache_by_pathlist(['/'])

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
        else:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("参数异常"))


#####
urls = [
    # 分类管理
    (r"/admin/category", CategoryController),
]
