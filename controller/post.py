# -*- coding: utf-8 -*-
import math

from core.common import BaseHandler, authorized, safe_encode, clear_cache_by_pathlist, quoted_string, getAttr
from model.archives import Archives
from model.posts import Posts
from model.categories import Categories
from model.comments import Comments
from model.tags import Tags
from setting import *

try:
    import json
except:
    import simplejson as json

if not debug:
    from sae.taskqueue import add_task


class PostController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        post_id = self.get_argument("post_id", '')

        obj = None
        if act == 'add':
            obj = Posts
            obj.post_id = ''
            obj.category_id = ''
            obj.category_name = ''
            obj.title = ''
            obj.content = ''
            obj.tags = ''
            obj.allow_comment = 1
            obj.top = 0
            obj.password = ''
            self.echo('admin_post_edit.html', {
            'title': "添加文章",
            'method': "/admin/posts?act=add",
            'categories': Categories.get_all_kv(),
            'tags': Tags.get_all_tag_name(),
            'obj': obj,
            }, layout='_layout_admin.html')
            return
        elif act == 'edit':
            if post_id:
                obj = Posts.get(post_id)
                self.echo('admin_post_edit.html', {
                'title': "编辑文章",
                'method': "/admin/posts?act=edit",
                'categories': Categories.get_all_kv(),
                'tags': Tags.get_all_tag_name(),
                'obj': obj,
                }, layout='_layout_admin.html')
                return
        elif act == 'del':
            if post_id:
                oldobj = Posts.get(post_id)
                Archives.remove_post_from_archive(post_id=post_id)
                Posts.delete(post_id)
                cache_key_list = ['/', 'post:%s' % post_id, 'cat:%s' % quoted_string(oldobj.category)]
                clear_cache_by_pathlist(cache_key_list)
                clear_cache_by_pathlist(['post:%s' % post_id])

                Posts.delete(post_id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return

        # 文章列表
        page = self.get_argument("page", 1)
        posts = Posts.get_paged(page, getAttr('ADMIN_POST_NUM'))
        categories = Categories.get_all_kv()
        total = math.ceil(Posts.count_all() / int(getAttr('ADMIN_POST_NUM')))
        if page == 1:
            self.echo('admin_post_list.html', {
            'title': "文章链接",
            'objs': posts,
            'categories': categories,
            'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
            'list': posts,
            'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return

    @authorized()
    def post(self):
        rspd = {"status": 200, "msg": "OK"}
        try:
            tf = {'true': 1, 'false': 0}
            act = self.get_argument("act", '').encode('utf-8')
            post_dic = {
            'category_id': self.get_argument("category_id", '-').encode('utf-8'),
            'user_id': self.get_secure_cookie("user_id"),
            'title': self.get_argument("title").encode('utf-8'),
            'digest': '-',
            'content': self.get_argument("content").encode('utf-8'),
            'image_url': '-',
            'tags': ','.join(self.get_arguments("tag")),
            'allow_comment': tf[self.get_argument("clo", 'false')],
            'top': tf[self.get_argument("top", 'false')],
            'password': self.get_argument("password", '').encode('utf-8'),
            'salt': '-',
            }
        except:
            rspd['status'] = 500
            rspd['msg'] = "用户名、邮箱均为必填项！"
            self.write(json.dumps(rspd))
            return

        if act == 'add':
            Posts.create(post_dic)
        elif act == 'edit':
            post_dic['post_id'] = int(self.get_argument("post_id", ""))
            Posts.update(post_dic)

        clear_cache_by_pathlist(['/'])

        if not debug:
            add_task('default', '/task/pingrpctask')

        self.set_header("Content-Type", "application/json")
        rspd['msg'] = "成功保存文章！"
        self.write(json.dumps(rspd))


class CommentController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        post_id = self.get_argument("id", '')

        obj = None
        if act == 'del':
            if post_id:
                Posts.delete(post_id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'edit':
            if post_id:
                obj = Posts.get(post_id)
                clear_cache_by_pathlist(['/'])

        # 文章列表
        page = self.get_argument("page", 1)
        posts = Posts.get_paged(page, getAttr('ADMIN_POST_NUM'))
        total = math.ceil(Posts.count_all() / float(getAttr('ADMIN_POST_NUM')))
        if page == 1:
            self.echo('admin_post_list.html', {
            'title': "文章链接",
            'objs': posts,
            'obj': obj,
            'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
            'list': posts,
            'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return

    @authorized()
    def post(self):
        act = self.get_argument("act", '')
        if act == 'findid':
            eid = self.get_argument("id", '')
            self.redirect('%s/admin/comment/%s' % (BASE_URL, eid))
            return

        tf = {'true': 1, 'false': 0}
        post_dic = {
        'author': self.get_argument("author"),
        'email': self.get_argument("email", ''),
        'content': safe_encode(self.get_argument("content").replace('\r', '\n')),
        'url': self.get_argument("url", ''),
        'visible': self.get_argument("visible", 'false'),
        'id': id
        }
        post_dic['visible'] = tf[post_dic['visible'].lower()]

        Comments.update(post_dic)
        clear_cache_by_pathlist(['post:%s' % id])
        self.redirect('%s/admin/comment/%s' % (BASE_URL, id))
        return


#####
urls = [
    # 文章相关
    (r"/admin/posts", PostController),
    (r"/admin/comment/(\d*)", CommentController),
]
