# -*- coding: utf-8 -*-
import time
from hashlib import md5

from core.common import getAttr
from core.utils.random_utils import random_string
from model import mdb, sdb

_author__ = 'baitao.ji'


def user_format(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
    return objs


class Users():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_user`')[0]['num']

    def create(self, params):
        if params['user_name'] and params['email']:
            user = Users.get_by_name_or_email(params['user_name'], params['email'])
            if not user:
                password = random_string(16)
                salt = random_string(8)
                password += salt
                sql = "insert into `cms_user` (`user_name`,`email`, `password`, `salt`, `status`)" \
                      " values(%s,%s,%s,%s,%s)"
                mdb._ensure_connected()
                mdb.execute(sql, params['user_name'], params['email'],
                            md5(password.encode('utf-8')).hexdigest(), salt, params['status'])
                return password
        return None

    def delete(self, user_id):
        mdb._ensure_connected()
        sql = "DELETE FROM `cms_user` WHERE `user_id`=%s"
        mdb.execute(sql, user_id)

    def update(self, params):
        if params['user_id']:
            sql = "update `cms_user` set `status`=%s" % params['status']
            if params['user_name'] != '':
                sql += ", `user_name` = \'%s\'" % params['user_name']
            if params['email'] != '':
                sql += ", `email` = \'%s\'" % params['email']
            if params['password'] and params['password'] != '':
                salt = random_string(8)
                params['password'] += salt
                sql += ", `password` = \'%s\', `salt` = \'%s\'" % (md5(params['password']).hexdigest(), salt)
            sql += " where `user_id` = \'%s\' LIMIT 1" % params['user_id']
            mdb._ensure_connected()
            return mdb.execute(sql)
        else:
            return None

    def update_user_audit(self, user_id, status=''):
        sql = "update `cms_user` set `status` = %s where `user_id` = %s LIMIT 1"
        mdb._ensure_connected()
        return mdb.execute(sql, status, user_id)

    def get(self, user_id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_user` WHERE `user_id` = %s LIMIT 1' % user_id)

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_user`')

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_USER_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `cms_user` ORDER BY `user_id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return user_format(sdb.query(sql))

    def check_has_user(self):
        sdb._ensure_connected()
        return sdb.get('SELECT `user_id` FROM `cms_user` LIMIT 1')

    def get_by_name_or_email(self, name, email=None):
        if not email:
            email = name
        sql = "SELECT * FROM `cms_user` WHERE `user_name` = \'%s\' or `email` = \'%s\' LIMIT 1"
        sdb._ensure_connected()
        return sdb.get(sql % (name, email))

    def check_name_email(self, user_name='', email=''):
        sql = "SELECT * FROM `cms_user` WHERE `user_name` = %s and `email` = %s and status=1 and deleted=0 LIMIT 1"
        sdb._ensure_connected()
        user = sdb.get(sql, user_name, email)
        if user:
            return True
        else:
            return False

    def check_user_or_email_password(self, name_or_email='', pw=''):
        if name_or_email and pw:
            user = self.get_by_name_or_email(name_or_email)
            return user is not None and user.status == 1 and user.password == pw
        else:
            return False

    def get_role(self, user_id):
        sql = "SELECT role_name FROM `cms_role` left join `cms_user_role` " \
              "on `cms_role`.role_id = `cms_user_role`.role_id and user_id = %s"
        sdb._ensure_connected()
        return sdb.query(sql, user_id)


Users = Users()