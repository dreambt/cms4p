# -*- coding: utf-8 -*-
from hashlib import md5
import random
import math

from tornado import escape
import tornado
from tornado.database import OperationalError
from core import dthandler

from core.common import BaseHandler, authorized, clear_cache_by_pathlist, getAttr, sendEmail
from core.utils.random_utils import random_string
from model.articles import Articles
from model.users import Users
from setting import *

try:
    import json
except:
    import simplejson as json


class UserController(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act", '').encode('utf-8')
        user_id = self.get_argument("id", '').encode('utf-8')

        obj = None
        if act == 'add':
            obj = Users
            obj.user_id = ''
            obj.user_name = ''
            obj.email = ''
            obj.status = 1
            self.echo('admin_user_edit.html', {
                'title': "添加用户",
                'method': "/admin/users?act=add",
                'obj': obj,
            }, layout='_layout_admin.html')
            return
        elif act == 'edit':
            if user_id:
                obj = Users.get(user_id)
                self.echo('admin_user_edit.html', {
                    'title': "编辑用户",
                    'method': "/admin/users?act=edit",
                    'obj': obj,
                }, layout='_layout_admin.html')
                return
        elif act == 'del':
            if user_id:
                Users.delete(user_id)
                clear_cache_by_pathlist(['/'])
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return

        # 用户列表
        page = self.get_argument("page", 1)
        category = Users.get_paged(page, getAttr('ADMIN_USER_NUM'))
        total = math.ceil(Users.count_all() / float(getAttr('ADMIN_USER_NUM')))
        if page == 1:
            self.echo('admin_user_list.html', {
                'title': "用户列表",
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
            self.write(json.dumps(result, default=dthandler))
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
            password = Users.create(params)
            # sub = {
            #     "%website%": [getAttr("SITE_TITLE").encode('utf-8')],
            #     "%url%": [getAttr("BASE_URL")],
            #     "%name%": [user_name],
            #     "%password%": [password]
            # }
            # sendTemplateEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), sub, str(email))
            sendEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), u"您的新密码是：" + password + u"<br /><br />请及时登录并修改密码！",
                      str(email))
        elif act == 'edit' and user_id is not None:
            Users.update(params)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))


class RePassword(BaseHandler):
    def get(self):
        self.echo('admin_repass.html')

    def post(self):
        self.set_header("Content-Type", "application/json")
        try:
            user_name = self.get_argument("name")
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
            if not Users.check_user_or_email_password(user_name_cookie, user_pw_cookie):
                self.write(json.dumps("重置密码失败！"))
                return

        if user_name and email and Users.check_name_email(user_name, email):
            password = random_string(16)
            params = {'user_name': user_name, 'email': email, 'password': password}
            Users.update(params)
            # sub = {
            #     "%website%": [getAttr("SITE_TITLE").encode('utf-8')],
            #     "%url%": [getAttr("BASE_URL")],
            #     "%name%": [user_name],
            #     "%password%": [password]
            # }
            #sendTemplateEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), sub, str(email))
            sendEmail(u"密码重置通知 - " + getAttr('SITE_TITLE'), u"您的新密码是：" + password + u"<br /><br />请及时登录并修改密码！", str(email))

            self.write(json.dumps("OK"))
            return
        else:
            self.write(json.dumps("重置密码失败！"))
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
                old_user = Users.get_by_name_or_email(username)
                oldPassword = md5(oldPassword.encode('utf-8') + old_user.salt.encode('utf-8')).hexdigest()
                if oldPassword == old_user.password:
                    Users.update(username, None, newPassword)
                    user = Users.get(old_user.id)
                    self.set_secure_cookie('userpw', user.password, expires_days=1)
                    self.write(escape.json.dumps("OK"))
                    return
                else:
                    self.write(escape.json.dumps("更新用户失败！"))
                    pass
        self.write(escape.json.dumps("请认真填写必填项！"))
        return


#####
urls = [
    # 用户管理
    (r"/admin/users", UserController),
    (r"/admin/repass_user", RePassword),
    (r"/admin/profile", EditProfile),
]
