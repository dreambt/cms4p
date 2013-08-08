# -*- coding: utf-8 -*-
import time
import math

from core.common import BaseHandler, authorized, safe_encode, clear_cache_by_pathlist, quoted_string, genArchive, set_count, increment, getAttr
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


class AddPost(BaseHandler):
    @authorized()
    def post(self):
        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'ok'}

        try:
            tf = {'true': 0, 'false': 1}
            timestamp = int(time.time())
            post_dic = {
                'category': self.get_argument("cat", '-'),
                'title': self.get_argument("tit"),
                'content': self.get_argument("con"),
                'tags': ','.join(self.get_arguments("tag")),
                'closecomment': tf[self.get_argument("clo", 'false')],
                'password': self.get_argument("password", ''),
                'add_time': timestamp,
                'edit_time': timestamp,
                'archive': genArchive(),
            }
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填的三项'
            self.write(json.dumps(rspd))
            return

        postid = Posts.create(post_dic)
        if postid:
            keyname = 'pv_%s' % (str(postid))
            set_count(keyname, 0, 0)

            Categories.add_postid_to_cat(post_dic['category'], str(postid))
            Archives.add_postid_to_archive(genArchive(), str(postid))
            increment('Totalblog')

            if post_dic['tags']:
                Tags.add_postid_to_tags(post_dic['tags'].split(','), str(postid))

            rspd['status'] = 200
            rspd['msg'] = '文章发布成功'
            rspd['postid'] = postid
            rspd['method'] = "/admin/edit_post"
            clear_cache_by_pathlist(['/', 'cat:%s' % quoted_string(post_dic['category'])])

            if not debug:
                add_task('default', '/task/pingrpctask')

            self.write(json.dumps(rspd))
            return
        else:
            rspd['status'] = 500
            rspd['msg'] = '错误： 未知错误，请尝试重新提交'
            self.write(json.dumps(rspd))
            return


class PostController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        post_id = self.get_argument("id", '')

        obj = None
        if act == 'add':
            obj = Posts
            obj.id = ''
            obj.category = ''
            obj.title = ''
            obj.content = ''
            obj.tags = ''
            obj.closecomment = 0
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
        try:
            tf = {'true': 1, 'false': 0}
            act = self.get_argument("act", '').encode('utf-8')
            user_id = self.get_argument("user_id", '').encode('utf-8')
            user_name = self.get_argument("user_name", '').encode('utf-8')
            email = self.get_argument("email", '').encode('utf-8')
            status = tf[self.get_argument("status", 'false').encode('utf-8')]
        except:
            self.write(json.dumps("用户名、邮箱均为必填项！"))
            return

        params = {'user_id': user_id, 'user_name': user_name, 'email': email, 'password': None, 'status': status}
        if act == 'add' and user_name is not None and email is not None:
            password = Posts.create(params)
        elif act == 'edit' and user_id is not None:
            Posts.update(params)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))


class EditPost(BaseHandler):
    @authorized()
    def post(self, id=''):
        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'ok'}
        oldobj = Posts.get(id)

        try:
            tf = {'true': 0, 'false': 1}
            timestamp = int(time.time())
            post_dic = {
                'category': self.get_argument("cat", '-'),
                'title': self.get_argument("tit"),
                'content': self.get_argument("con"),
                'tags': ",".join(self.get_arguments("tag")),
                'closecomment': tf[self.get_argument("clo", 'false')],
                'password': self.get_argument("password", ''),
                'edit_time': timestamp,
                'id': id
            }

            if post_dic['tags']:
                tagslist = set([x.strip() for x in post_dic['tags'].split(',')])
                try:
                    tagslist.remove('')
                except:
                    pass
                if tagslist:
                    post_dic['tags'] = ','.join(tagslist)
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填的三项'
            self.write(json.dumps(rspd))
            return

        postid = Posts.update(post_dic)
        if postid:
            cache_key_list = ['/', 'post:%s' % id, 'cat:%s' % quoted_string(oldobj.category)]
            if oldobj.category != post_dic['category']:
                #cat changed 
                Categories.add_postid_to_cat(post_dic['category'], str(postid))
                Categories.remove_postid_from_cat(oldobj.category, str(postid))
                cache_key_list.append('cat:%s' % quoted_string(post_dic['category']))

            if oldobj.tags != post_dic['tags']:
                #tag changed 
                old_tags = set(oldobj.tags.split(','))
                new_tags = set(post_dic['tags'].split(','))

                removed_tags = old_tags - new_tags
                added_tags = new_tags - old_tags

                if added_tags:
                    Tags.add_postid_to_tags(added_tags, str(postid))

                if removed_tags:
                    Tags.remove_postid_from_tags(removed_tags, str(postid))

            clear_cache_by_pathlist(cache_key_list)
            rspd['status'] = 200
            rspd['msg'] = '文章编辑成功'
            rspd['postid'] = postid
            self.write(json.dumps(rspd))
            return
        else:
            rspd['status'] = 500
            rspd['msg'] = '错误： 未知错误，请尝试重新提交'
            self.write(json.dumps(rspd))
            return


class DelPost(BaseHandler):
    @authorized()
    def get(self, id=''):
        try:
            if id:
                oldobj = Posts.get(id)
                Categories.remove_postid_from_cat(oldobj.category, str(id))
                Archives.remove_postid_from_archive(oldobj.archive, str(id))
                Tags.remove_postid_from_tags(set(oldobj.tags.split(',')), str(id))
                Posts.delete(id)
                increment('Totalblog', NUM_SHARDS, -1)
                cache_key_list = ['/', 'post:%s' % id, 'cat:%s' % quoted_string(oldobj.category)]
                clear_cache_by_pathlist(cache_key_list)
                clear_cache_by_pathlist(['post:%s' % id])
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps("OK"))
                return
        except:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("error"))
            return


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
    (r"/admin/add_post", AddPost),
    (r"/admin/edit_post/(\d*)", EditPost),
    (r"/admin/posts", PostController),
    (r"/admin/del_post/(\d+)", DelPost),
    (r"/admin/comment/(\d*)", CommentController),
]
