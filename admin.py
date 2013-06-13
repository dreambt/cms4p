# -*- coding: utf-8 -*-
import StringIO
from hashlib import md5
import random
import re
import time
import math

from sae.storage import Bucket
from tornado import escape
import tornado
from tornado.database import OperationalError

from common import BaseHandler, authorized, safe_encode, clear_cache_by_pathlist, quoted_string, clear_all_cache, genArchive, setAttr, clearAllKVDB, set_count, increment, getAttr, sendEmail
from helpers import generate_random
from setting import *
from extensions.imagelib import Recaptcha, Thumbnail
from model import Article, Comment, Link, Category, Tag, User, MyData, Archive


try:
    import json
except:
    import simplejson as json

if not debug:
    import sae.mail
    from sae.taskqueue import add_task

bucket = Bucket(DEFAULT_BUCKET)


def put_saestorage(file_name='', data='', expires='365', con_type=None, encoding=None, domain_name=DEFAULT_BUCKET):
    bucket.put_object(file_name, data)
    return bucket.generate_url(file_name)
    #s = sae.storage.Client()
    #ob = sae.storage.Object(data=data, cache_control='access plus %s day' % expires, content_type=con_type,
    #                        content_encoding=encoding)
    #return s.put(domain_name, str(datetime.now().strftime("%Y%m") + "/" + file_name), ob)
    #return s.put(domain_name, file_name, ob)


def get_saestorage(domain_name=DEFAULT_BUCKET):
    #s = sae.storage.Client()
    #filelist = s.list(domain_name)
    filelist = bucket.list()
    #total_count = len(filelist)
    return filelist


class HomePage(BaseHandler):
    @authorized()
    def get(self):
        output = self.render('admin_index.html', {
            'title': "后台首页",
            'keywords': getAttr('KEYWORDS'),
            'description': getAttr('SITE_DECR'),
            'test': '',
        }, layout='_layout_admin.html')
        self.write(output)
        return output


class Login(BaseHandler):
    def get(self):
        self.echo('admin_login.html')

    def post(self):
        self.set_header("Content-Type", "application/json")

        try:
            name = self.get_argument("name")
            password = self.get_argument("password")
            captcha = self.get_argument("captcha")
        except:
            self.write(json.dumps("用户名、密码、验证码均为必填项！"))
            return

        if self.get_secure_cookie("captcha") != captcha:
            self.write(json.dumps("验证码填写错误或用户不存在！"))
            return

        has_user = User.get_user_by_name(name)
        if not has_user:
            has_user = User.get_user_by_email(name)
            name = has_user.name
        if has_user:
            password += has_user.salt
            password = md5(password.encode('utf-8')).hexdigest()
            if password == has_user.password:
                self.set_secure_cookie('username', name, expires_days=365)
                self.set_secure_cookie('userpw', password, expires_days=365)
                self.write(json.dumps("OK"))
                return
            else:
                self.write(json.dumps("权限验证失败或帐户不可用！"))
                return
        else:
            self.write(json.dumps("验证码填写错误或用户不存在！"))
            return


class Logout(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('%s/admin/login' % BASE_URL)


class Forbidden(BaseHandler):
    def get(self):
        self.write('Forbidden page')


class FileUpload(BaseHandler):
    @authorized()
    def post(self):
        self.set_header('Content-Type', 'text/html')
        rspd = {'status': 201, 'msg': 'ok'}
        max_size = 10240000  # 10MB
        fileupload = self.request.files['imgFile']
        if fileupload:
            myfile = fileupload[0]
            if not myfile['filename']:
                self.write(json.dumps(
                    {'error': 1, 'message': u'请选择要上传的文件'}
                ))
                return

            # if myfile.size > max_size:
            #     self.write(json.dumps(
            #         { 'error': 1, 'message': u'上传的文件大小不能超过 10 MB'}
            #     ))
            #     return

            file_type = myfile['filename'].split('.')[-1].lower()
            file_name = str(int(time.time() * 1000))
            mime_type = myfile['content_type']
            encoding = None

            # 缩放图片
            try:
                if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    new_file_name = "%s-thumb.%s" % (file_name, file_type)
                    img_data = Thumbnail(StringIO.StringIO(myfile['body'])).thumb((100, 100))
                    put_saestorage(file_name=new_file_name, data=img_data, expires='365',
                                   con_type=mime_type, encoding=encoding)
                    #im = Image.open(StringIO.StringIO(myfile['body']))
                    # im.show()
                    #width, height = im.size
                    #if width > 750:
                    #    ratio = 1.0 * height / width
                    #    new_height = int(750 * ratio)
                    #    new_size = (750, new_height)
                    #    out = im.resize(new_size, Image.ANTIALIAS)
                    #    myfile['body'] = out.toString('jpeg', 'RGB')
                    #    file_type = 'jpg'
                    #    print 750, new_height
                    #    new_file_name = "%s-thumb.%s" % (str(int(time.time())), file_type)
                    #else:
                    #    pass
                else:
                    pass
            except:
                pass

            try:
                new_file_name = "%s.%s" % (file_name, file_type)
                attachment_url = put_saestorage(file_name=new_file_name, data=myfile['body'], expires='365',
                                                con_type=mime_type, encoding=encoding)
            except:
                attachment_url = ''

            if attachment_url:
                rspd['status'] = 200
                rspd['error'] = 0
                rspd['filename'] = myfile['filename']
                rspd['url'] = attachment_url
            else:
                rspd['status'] = 500
                rspd['error'] = 1
                rspd['message'] = 'put_saestorage error, try it again.'
        else:
            rspd['message'] = 'No file uploaded'
        self.write(json.dumps(rspd))
        return


class FileManager(BaseHandler):
    @authorized()
    def get(self):
        file_list = get_saestorage()

        upload = {
            "moveup_dir_path": "",
            "current_dir_path": "/stor-stub/attachment/",
            "current_url": BASE_URL + "/stor-stub/attachment/",
            "file_list": [],
        }

        for dirfile in file_list:
            filesize = dirfile['length']
            filetype = dirfile['name'].split('.')[-1].lower()
            filename = dirfile['name']
            datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dirfile['datetime']))
            if re.match('gif|jpg|jpeg|png|bmp', filetype):
                is_photo = True
            else:
                is_photo = False
            file_list = {
                "is_dir": False,
                "has_file": False,
                "filesize": filesize,
                "dir_path": "/stor-stub/attachment/",
                "is_photo": is_photo,
                "filetype": filetype,
                "filename": filename,
                "datetime": datetime,
            }
            upload["file_list"].append(file_list)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(upload))
        return


class CategoryController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        id = self.get_argument("id", '')

        obj = None
        if act == 'del':
            if id:
                Category.delete_category(id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'edit':
            if id:
                obj = Category.get_category(id)

        # 分类列表
        page = self.get_argument("page", 1)
        category = Category.get_paged(page, getAttr('ADMIN_CATEGORY_NUM'))
        total = math.ceil(Category.count_all() / float(getAttr('ADMIN_CATEGORY_NUM')))
        if page == 1:
            self.echo('admin_category.html', {
                'title': "分类列表",
                'objs': category,
                'obj': obj,
                'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
                'list': category,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return

    @authorized()
    def post(self):
        act = self.get_argument("act", '')
        id = self.get_argument("id", '')
        name = self.get_argument("name", '')
        showtype = self.get_argument("showtype", '')
        sort = self.get_argument("sort", '0')

        if id and (name or sort):
            if act == 'add':
                Category.create_category(name)

            if act == 'edit':
                params = {'id': id, 'name': name, 'showtype': showtype, 'displayorder': sort}
                Category.update_cat(params)

            if act == 'del':
                Category.delete_category(id)

            clear_cache_by_pathlist(['/'])

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
        else:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("参数异常"))


class AddPost(BaseHandler):
    @authorized()
    def get(self):
        obj = Article
        obj.id = ''
        obj.category = ''
        obj.title = ''
        obj.content = ''
        obj.tags = ''
        obj.closecomment = 0
        obj.password = ''
        self.echo('admin_post_edit.html', {
            'title': "添加文章",
            'method': "/admin/add_post",
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_all_tag_name(),
            'obj': obj,
        }, layout='_layout_admin.html')

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
                'tags': ','.join(self.get_arguments("tag[]")),
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

        postid = Article.create_article(post_dic)
        if postid:
            keyname = 'pv_%s' % (str(postid))
            set_count(keyname, 0, 0)

            Category.add_postid_to_cat(post_dic['category'], str(postid))
            Archive.add_postid_to_archive(genArchive(), str(postid))
            increment('Totalblog')

            if post_dic['tags']:
                Tag.add_postid_to_tags(post_dic['tags'].split(','), str(postid))

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


class ListPost(BaseHandler):
    @authorized()
    def get(self):
        page = self.get_argument("page", 1)
        article = Article.get_paged(page, getAttr('ADMIN_POST_NUM'))
        total = math.ceil(Article.count_all() / float(getAttr('ADMIN_POST_NUM')))
        if page == 1:
            self.echo('admin_post_list.html', {
                'title': "文章列表",
                'objs': article,
                'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
                'list': article,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return


class EditPost(BaseHandler):
    @authorized()
    def get(self, id=''):
        obj = None
        if id:
            obj = Article.get_article(id)
        self.echo('admin_post_edit.html', {
            'title': "编辑文章",
            'method': "/admin/edit_post/" + id,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_all_tag_name(),
            'obj': obj
        }, layout='_layout_admin.html')

    @authorized()
    def post(self, id=''):
        act = self.get_argument("act", '')
        if act == 'findid':
            eid = self.get_argument("id", '')
            self.redirect('%s/admin/edit_post/%s' % (BASE_URL, eid))
            return

        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'ok'}
        oldobj = Article.get_article(id)

        try:
            tf = {'true': 0, 'false': 1}
            timestamp = int(time.time())
            post_dic = {
                'category': self.get_argument("cat", '-'),
                'title': self.get_argument("tit"),
                'content': self.get_argument("con"),
                'tags': ",".join(self.get_arguments("tag[]")),
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

        postid = Article.update_post_edit(post_dic)
        if postid:
            cache_key_list = ['/', 'post:%s' % id, 'cat:%s' % quoted_string(oldobj.category)]
            if oldobj.category != post_dic['category']:
                #cat changed 
                Category.add_postid_to_cat(post_dic['category'], str(postid))
                Category.remove_postid_from_cat(oldobj.category, str(postid))
                cache_key_list.append('cat:%s' % quoted_string(post_dic['category']))

            if oldobj.tags != post_dic['tags']:
                #tag changed 
                old_tags = set(oldobj.tags.split(','))
                new_tags = set(post_dic['tags'].split(','))

                removed_tags = old_tags - new_tags
                added_tags = new_tags - old_tags

                if added_tags:
                    Tag.add_postid_to_tags(added_tags, str(postid))

                if removed_tags:
                    Tag.remove_postid_from_tags(removed_tags, str(postid))

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
                oldobj = Article.get_article(id)
                Category.remove_postid_from_cat(oldobj.category, str(id))
                Archive.remove_postid_from_archive(oldobj.archive, str(id))
                Tag.remove_postid_from_tags(set(oldobj.tags.split(',')), str(id))
                Article.delete_post(id)
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
    def get(self, id=''):
        obj = None
        total = math.ceil(Comment.count_all() / float(getAttr('ADMIN_COMMENT_NUM')))
        if id:
            obj = Comment.get_comment(id)
            if obj:
                act = self.get_argument("act", '')
                if act == 'del':
                    Comment.delete_comment(id)
                    clear_cache_by_pathlist(['post:%d' % obj.postid])
                    self.set_header("Content-Type", "application/json")
                    self.write(json.dumps("OK"))
                    return
                else:
                    self.echo('admin_comment.html', {
                        'title': "评论管理",
                        'obj': obj,
                        'total': total,
                    }, layout='_layout_admin.html')
                    return

        # 评论列表
        page = self.get_argument("page", 1)
        comments = Comment.get_paged(page, getAttr('ADMIN_COMMENT_NUM'))
        if page == 1:
            self.echo('admin_comment.html', {
                'title': "评论管理",
                'obj': obj,
                'total': total,
                'comments': comments,
            }, layout='_layout_admin.html')
            return
        else:
            result = {
                'list': comments,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return


    @authorized()
    def post(self, id=''):
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

        Comment.update_comment(post_dic)
        clear_cache_by_pathlist(['post:%s' % id])
        self.redirect('%s/admin/comment/%s' % (BASE_URL, id))
        return


class LinkController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '')
        id = self.get_argument("id", '')

        obj = None
        if act == 'del':
            if id:
                Link.delete_link(id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'edit':
            if id:
                obj = Link.get_link(id)
                clear_cache_by_pathlist(['/'])

        # 友情链接列表
        page = self.get_argument("page", 1)
        links = Link.get_paged(page, getAttr('ADMIN_LINK_NUM'))
        total = math.ceil(Link.count_all() / float(getAttr('ADMIN_LINK_NUM')))
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
        act = self.get_argument("act", '')
        id = self.get_argument("id", '')
        name = self.get_argument("name", '')
        sort = self.get_argument("sort", '0')
        url = self.get_argument("url", '')

        if name and url:
            params = {'id': id, 'name': name, 'url': url, 'displayorder': sort}
            if act == 'add':
                Link.create_link(params)

            if act == 'edit':
                Link.update_link(params)

            clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))


class AddUser(BaseHandler):
    @authorized()
    def get(self):
        obj = User
        obj.id = ''
        obj.name = ''
        obj.email = ''
        obj.status = 1
        self.echo('admin_user_edit.html', {
            'title': "添加用户",
            'method': "/admin/add_user",
            'obj': obj,
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'OK'}

        try:
            tf = {'true': 1, 'false': 0}
            email = self.get_argument("email", '')
            name = self.get_argument("username", '')
            pw = ''.join(random.sample('zAyBxCwDvEuFtGsHrIqJpKoLnMmNlOkPjQiRhSgTfUeVdWcXbYaZ1928374650', 16))
            status = tf[self.get_argument("status", 'true')]
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填项'
            self.write(json.dumps(rspd))
            return

        try:
            userid = User.create_user(name, email, pw, status)
            if userid:
                sendEmail(u"新用户注册通知 - " + SITE_TITLE, u"您的密码是：" + pw + u"<br />请及时登录并修改密码！", email)

                rspd['status'] = 200
                rspd['msg'] = '创建用户成功，已邮件通知该用户！'
                rspd['userid'] = userid
                rspd['method'] = "/admin/edit_user"
                clear_cache_by_pathlist(['/', 'user:%s' % str(userid)])
            else:
                rspd['status'] = 500
                rspd['msg'] = '错误： 通知邮件发送失败，请稍后重试'
        except OperationalError:
            rspd['status'] = 500
            rspd['msg'] = '错误： 该 Email 地址已被占用，请尝试重新提交'
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 未知错误，请尝试重新提交'

        self.write(json.dumps(rspd))
        return


class ListUser(BaseHandler):
    @authorized()
    def get(self):
        page = self.get_argument("page", 1)
        limit = getAttr('ADMIN_USER_NUM')
        users = User.get_paged(page, limit)
        total = math.ceil(Article.count_all() / float(limit))
        if page == 1:
            self.echo('admin_user_list.html', {
                'title': "用户列表",
                'objs': users,
                'total': total,
            }, layout='_layout_admin.html')
        else:
            result = {
                'list': users,
                'total': total,
            }
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
            return


class EditUser(BaseHandler):
    @authorized()
    def get(self, id=''):
        obj = None
        if id:
            obj = User.get_user(id)
        self.echo('admin_user_edit.html', {
            'title': "编辑用户",
            'method': "/admin/edit_user/" + id,
            'obj': obj
        }, layout='_layout_admin.html')

    @authorized()
    def post(self, id=''):
        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'ok'}

        try:
            tf = {'true': 1, 'false': 0}
            status = tf[self.get_argument("status", 'false')]
            User.update_user_audit(id, status)
            rspd['status'] = 200
            rspd['msg'] = '用户编辑成功'
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误：注意必填项'

        self.write(json.dumps(rspd))
        return


class DelUser(BaseHandler):
    @authorized()
    def get(self, id=''):
        try:
            if id:
                user = User.get_user(id)
                articles = Article.get_article_by_author(user.name)
                for article in articles:
                    Article.update_post_edit_author(article.id, "admin")
                User.delete_user(id)
                cache_key_list = ['/', 'user:%s' % id]
                clear_cache_by_pathlist(cache_key_list)
                self.set_header("Content-Type", "application/json")
                self.write(json.dumps("OK"))
                return
        except:
            raise tornado.web.HTTPError(500)


class RePassword(BaseHandler):
    def get(self):
        self.echo('admin_repass.html')

    def post(self):
        self.set_header("Content-Type", "application/json")
        try:
            name = self.get_argument("name")
            email = self.get_argument("email")
            captcha = self.get_argument("captcha", "")
        except:
            self.write(json.dumps("用户名、邮箱、验证码均为必填项！"))
            return

        if captcha:
            if self.get_secure_cookie("captcha") != captcha:
                self.write(json.dumps("验证码填写错误！"))
                return
        else:
            user_name_cookie = self.get_secure_cookie('username')
            user_pw_cookie = self.get_secure_cookie('userpw')
            if not User.check_user_password(user_name_cookie, user_pw_cookie):
                self.write(json.dumps("重置密码失败！"))
                return

        if name and email and User.check_name_email(name, email):
            pw = "".join(random.sample('zAyBxCwDvEuFtGsHrIqJpKoLnMmNlOkPjQiRhSgTfUeVdWcXbYaZ1928374650', 16))
            User.update_user(name, email, pw)
            sub = {
                "%website%": [getAttr("SITE_TITLE").encode('utf-8')],
                "%url%": [getAttr("BASE_URL")],
                "%name%": [name],
                "%password%": [pw]
            }
            #sendTemplateEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), sub, str(email))
            sendEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), u"您的新密码是：" + pw + u"<br /><br />请及时登录并修改密码！", str(email))

            self.write(json.dumps("OK"))
            return
        else:
            self.write(json.dumps("重置密码失败！"))
            return


class BlogSetting(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting.html', {
            'title': "站点信息",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        value = self.get_argument("SITE_TITLE", '')
        if value:
            setAttr('SITE_TITLE', value)
        value = self.get_argument("SITE_TITLE2", '')
        if value:
            setAttr('SITE_TITLE2', value)

        value = self.get_argument("SITE_SUB_TITLE", '')
        if value:
            setAttr('SITE_SUB_TITLE', value)

        value = self.get_argument("KEYWORDS", '')
        if value:
            setAttr('KEYWORDS', value)

        value = self.get_argument("SITE_DECR", '')
        if value:
            setAttr('SITE_DECR', value)

        value = self.get_argument("ADMIN_NAME", '')
        if value:
            setAttr('ADMIN_NAME', value)

        value = self.get_argument("MOVE_SECRET", '')
        if value:
            setAttr('MOVE_SECRET', value)

        value = self.get_argument("NOTICE_MAIL", '')
        if value:
            setAttr('NOTICE_MAIL', value)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting2(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting2.html', {
            'title': "邮箱配置",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        value = self.get_argument("MAIL_FROM", '')
        if value:
            setAttr('MAIL_FROM', value)

        value = self.get_argument("MAIL_KEY", '')
        if value:
            setAttr('MAIL_KEY', value)

        value = self.get_argument("MAIL_SMTP", '')
        if value:
            setAttr('MAIL_SMTP', value)

        value = self.get_argument("MAIL_PORT", '')
        if value:
            setAttr('MAIL_PORT', value)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting3(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting3.html', {
            'title': "详细参数",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        # 文章相关
        EACH_PAGE_POST_NUM = self.get_argument("EACH_PAGE_POST_NUM", '')
        if EACH_PAGE_POST_NUM:
            setAttr('EACH_PAGE_POST_NUM', EACH_PAGE_POST_NUM)

        SHORTEN_CONTENT_WORDS = self.get_argument("SHORTEN_CONTENT_WORDS", '')
        if SHORTEN_CONTENT_WORDS:
            setAttr('SHORTEN_CONTENT_WORDS', SHORTEN_CONTENT_WORDS)

        DESCRIPTION_CUT_WORDS = self.get_argument("DESCRIPTION_CUT_WORDS", '')
        if DESCRIPTION_CUT_WORDS:
            setAttr('DESCRIPTION_CUT_WORDS', DESCRIPTION_CUT_WORDS)

        RELATIVE_POST_NUM = self.get_argument("RELATIVE_POST_NUM", '')
        if RELATIVE_POST_NUM:
            setAttr('RELATIVE_POST_NUM', RELATIVE_POST_NUM)

        # 评论相关
        EACH_PAGE_COMMENT_NUM = self.get_argument("EACH_PAGE_COMMENT_NUM", '')
        if EACH_PAGE_COMMENT_NUM:
            setAttr('EACH_PAGE_COMMENT_NUM', EACH_PAGE_COMMENT_NUM)

        RECENT_COMMENT_NUM = self.get_argument("RECENT_COMMENT_NUM", '')
        if RECENT_COMMENT_NUM:
            setAttr('RECENT_COMMENT_NUM', RECENT_COMMENT_NUM)

        RECENT_COMMENT_CUT_WORDS = self.get_argument("RECENT_COMMENT_CUT_WORDS", '')
        if RECENT_COMMENT_CUT_WORDS:
            setAttr('RECENT_COMMENT_CUT_WORDS', RECENT_COMMENT_CUT_WORDS)

        MAX_COMMENT_NUM_A_DAY = self.get_argument("MAX_COMMENT_NUM_A_DAY", '')
        if MAX_COMMENT_NUM_A_DAY:
            setAttr('MAX_COMMENT_NUM_A_DAY', MAX_COMMENT_NUM_A_DAY)

        COMMENT_DEFAULT_VISIBLE = self.get_argument("COMMENT_DEFAULT_VISIBLE", '')
        if COMMENT_DEFAULT_VISIBLE:
            setAttr('COMMENT_DEFAULT_VISIBLE', COMMENT_DEFAULT_VISIBLE)

        # 其他设置
        LINK_NUM = self.get_argument("LINK_NUM", '')
        if LINK_NUM:
            setAttr('LINK_NUM', LINK_NUM)

        HOT_TAGS_NUM = self.get_argument("HOT_TAGS_NUM", '')
        if HOT_TAGS_NUM:
            setAttr('HOT_TAGS_NUM', HOT_TAGS_NUM)

        MAX_ARCHIVES_NUM = self.get_argument("MAX_ARCHIVES_NUM", '')
        if MAX_ARCHIVES_NUM:
            setAttr('MAX_ARCHIVES_NUM', MAX_ARCHIVES_NUM)

        clear_all_cache()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting4(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting4.html', {
            'title': "广告统计",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        ANALYTICS_CODE = self.get_argument("ANALYTICS_CODE", '')
        if ANALYTICS_CODE:
            setAttr('ANALYTICS_CODE', ANALYTICS_CODE)

        ADSENSE_CODE1 = self.get_argument("ADSENSE_CODE1", '')
        if ADSENSE_CODE1:
            setAttr('ADSENSE_CODE1', ADSENSE_CODE1)

        ADSENSE_CODE2 = self.get_argument("ADSENSE_CODE2", '')
        if ADSENSE_CODE2:
            setAttr('ADSENSE_CODE2', ADSENSE_CODE2)

        clear_all_cache()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


# 后台相关
class BlogSetting5(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting5.html', {
            'title': "详细参数",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        ADMIN_CATEGORY_NUM = self.get_argument("ADMIN_CATEGORY_NUM", '')
        if ADMIN_CATEGORY_NUM:
            setAttr('ADMIN_CATEGORY_NUM', ADMIN_CATEGORY_NUM)

        ADMIN_POST_NUM = self.get_argument("ADMIN_POST_NUM", '')
        if ADMIN_POST_NUM:
            setAttr('ADMIN_POST_NUM', ADMIN_POST_NUM)

        ADMIN_COMMENT_NUM = self.get_argument("ADMIN_COMMENT_NUM", '')
        if ADMIN_COMMENT_NUM:
            setAttr('ADMIN_COMMENT_NUM', ADMIN_COMMENT_NUM)

        ADMIN_USER_NUM = self.get_argument("ADMIN_USER_NUM", '')
        if ADMIN_USER_NUM:
            setAttr('ADMIN_USER_NUM', ADMIN_USER_NUM)

        ADMIN_LINK_NUM = self.get_argument("ADMIN_LINK_NUM", '')
        if ADMIN_LINK_NUM:
            setAttr('ADMIN_LINK_NUM', ADMIN_LINK_NUM)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class EditProfile(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_profile.html', {
            'title': "个人资料",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        self.set_header("Content-Type", "application/json")
        oldPassword = self.get_argument("oldPassword", '')
        newPassword = self.get_argument("newPassword", '')
        newPassword2 = self.get_argument("newPassword2", '')
        if oldPassword and newPassword and newPassword2:
            if newPassword == newPassword2:
                username = self.get_secure_cookie('username')
                old_user = User.get_user_by_name(username)
                oldPassword = md5(oldPassword.encode('utf-8')+old_user.salt.encode('utf-8')).hexdigest()
                if oldPassword == old_user.password:
                    User.update_user(username, None, newPassword)
                    user = User.get_user(old_user.id)
                    self.set_secure_cookie('userpw', user.password, expires_days=1)
                    self.write(escape.json.dumps("OK"))
                    return
                else:
                    self.write(escape.json.dumps("更新用户失败！"))
                    pass
        self.write(escape.json.dumps("请认真填写必填项！"))
        return


# TODO KVDB 管理
class KVDBAdmin(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_kvdb.html', {
            'title': "KVDB 管理",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        self.redirect('%s/admin/kvdb' % BASE_URL)
        return


class FlushData(BaseHandler):
    @authorized()
    def post(self):
        act = self.get_argument("act", '')
        if act == 'flush':
            MyData.flush_all_data()
            clear_all_cache()
            clearAllKVDB()
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'flushcache':
            clear_all_cache()
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return


class PingRPCTask(BaseHandler):
    def get(self):
        for n in range(len(XML_RPC_ENDPOINTS)):
            add_task('default', '%s/task/pingrpc/%d' % (BASE_URL, n))
        self.write(str(time.time()))

    post = get


class PingRPC(BaseHandler):
    def get(self, n=0):
        import urllib2

        pingstr = self.render('rpc.xml', {'article_id': Article.get_max_id()})

        headers = {
            'User-Agent': 'request',
            'Content-Type': 'text/xml',
            'Content-length': str(len(pingstr))
        }

        req = urllib2.Request(
            url=XML_RPC_ENDPOINTS[int(n)],
            headers=headers,
            data=pingstr,
        )
        try:
            content = urllib2.urlopen(req).read()
            tip = 'Ping ok' + content
        except:
            tip = 'ping erro'

        self.write(str(time.time()) + ": " + tip)
        #add_task('default', '%s/task/sendmail'%BASE_URL, urlencode({'subject': tip, 'content': tip + " " + str(n)}))

    post = get


class SendMail(BaseHandler):
    def post(self):
        subject = self.get_argument("subject", '')
        content = self.get_argument("content", '')

        if subject and content:
            sendEmail(subject, content, getAttr('NOTICE_MAIL'))


# 初始化一些参数
def Init():
    setAttr('SITE_TITLE', SITE_TITLE)
    setAttr('SITE_TITLE2', SITE_TITLE2)
    setAttr('SITE_SUB_TITLE', SITE_SUB_TITLE)
    setAttr('KEYWORDS', KEYWORDS)
    setAttr('SITE_DECR', SITE_DECR)
    setAttr('ADMIN_NAME', ADMIN_NAME)
    setAttr('NOTICE_MAIL', NOTICE_MAIL)
    setAttr('MOVE_SECRET', MOVE_SECRET)

    setAttr('MAIL_FROM', MAIL_FROM)
    setAttr('MAIL_KEY', MAIL_KEY)
    setAttr('MAIL_SMTP', MAIL_SMTP)
    setAttr('MAIL_PORT', MAIL_PORT)

    setAttr('EACH_PAGE_POST_NUM', EACH_PAGE_POST_NUM)
    setAttr('EACH_PAGE_COMMENT_NUM', EACH_PAGE_COMMENT_NUM)
    setAttr('RELATIVE_POST_NUM', RELATIVE_POST_NUM)
    setAttr('SHORTEN_CONTENT_WORDS', SHORTEN_CONTENT_WORDS)
    setAttr('DESCRIPTION_CUT_WORDS', DESCRIPTION_CUT_WORDS)

    setAttr('RECENT_COMMENT_NUM', RECENT_COMMENT_NUM)
    setAttr('RECENT_COMMENT_CUT_WORDS', RECENT_COMMENT_CUT_WORDS)
    setAttr('MAX_COMMENT_NUM_A_DAY', MAX_COMMENT_NUM_A_DAY)
    setAttr('COMMENT_DEFAULT_VISIBLE', COMMENT_DEFAULT_VISIBLE)

    setAttr('LINK_NUM', LINK_NUM)
    setAttr('HOT_TAGS_NUM', HOT_TAGS_NUM)
    setAttr('MAX_ARCHIVES_NUM', MAX_ARCHIVES_NUM)

    setAttr('ANALYTICS_CODE', ANALYTICS_CODE)
    setAttr('ADSENSE_CODE1', ADSENSE_CODE1)
    setAttr('ADSENSE_CODE2', ADSENSE_CODE2)

    setAttr('ADMIN_CATEGORY_NUM', ADMIN_CATEGORY_NUM)
    setAttr('ADMIN_POST_NUM', ADMIN_POST_NUM)
    setAttr('ADMIN_COMMENT_NUM', ADMIN_COMMENT_NUM)
    setAttr('ADMIN_USER_NUM', ADMIN_USER_NUM)
    setAttr('ADMIN_LINK_NUM', ADMIN_LINK_NUM)


class Install(BaseHandler):
    def get(self):
        Init()
        self.echo('admin_install.html')
        # try:
        #     self.write('如果出现错误请尝试刷新本页。')
        #     has_user = User.check_has_user()
        #     if has_user:
        #         self.write('博客已经成功安装了，你可以直接 <a href="/admin/flushdata">清空网站数据</a>')
        #     else:
        #         self.write('博客数据库已经建立，现在就去 <a href="/admin/">设置一个管理员帐号</a>')
        # except:
        #     try:
        #         MyData.creat_table()
        #         Init()  # 初始化系统参数
        #     except:
        #         pass
        #     self.write('博客已经成功安装了，现在就去 <a href="/admin/">设置一个管理员帐号</a>')

    def post(self):
        pass


class GetCaptcha(BaseHandler):
    def get(self):
        text = generate_random(4)
        self.set_secure_cookie("captcha", text)

        strIO = Recaptcha(text)

        # ,mimetype='image/png'
        self.set_header("Content-Type", "image/png")
        self.write(strIO.read())
        return


class NotFoundPage(BaseHandler):
    def get(self):
        self.set_status(404)
        self.echo('error.html', {
            'page': '404',
            'title': "Can't find out this URL",
            'h2': 'Oh, my god!',
            'msg': '<script type="text/javascript" src="http://www.qq.com/404/search_children.js?edition=small" charset="utf-8"></script>'
        })

#####
urls = [
    (r"/admin/", HomePage),
    (r"/admin/login", Login),
    (r"/admin/logout", Logout),
    (r"/admin/403", Forbidden),
    # 分类管理
    (r"/admin/category", CategoryController),
    # 文章相关
    (r"/admin/add_post", AddPost),
    (r"/admin/edit_post/(\d*)", EditPost),
    (r"/admin/list_post", ListPost),
    (r"/admin/del_post/(\d+)", DelPost),
    (r"/admin/comment/(\d*)", CommentController),
    # 用户管理
    (r"/admin/add_user", AddUser),
    (r"/admin/edit_user/(\d*)", EditUser),
    (r"/admin/list_user", ListUser),
    (r"/admin/del_user/(\d+)", DelUser),
    (r"/admin/repass_user", RePassword),
    # 文件上传及管理
    (r"/admin/fileupload", FileUpload),
    (r"/admin/filelist", FileManager),
    (r"/admin/links", LinkController),
    (r"/admin/setting", BlogSetting),
    (r"/admin/setting2", BlogSetting2),
    (r"/admin/setting3", BlogSetting3),
    (r"/admin/setting4", BlogSetting4),
    (r"/admin/setting5", BlogSetting5),  # 后台设置
    (r"/admin/profile", EditProfile),
    (r"/admin/kvdb", KVDBAdmin),
    (r"/admin/flushdata", FlushData),
    (r"/task/pingrpctask", PingRPCTask),
    (r"/task/pingrpc/(\d+)", PingRPC),
    (r"/task/sendmail", SendMail),
    (r"/captcha/", GetCaptcha),
    (r"/install", Install),
    (r".*", NotFoundPage)
]
