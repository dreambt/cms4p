# -*- coding: utf-8 -*-
import time
from hashlib import md5

from core.common import getAttr
from core.utils.random_utils import random_string
from model.base import mdb, sdb

_author__ = 'baitao.ji'


def user_format(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
    return objs


class User():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_user`')[0]['num']

    def create(self, user_name='', email='', pw='', status=1):
        if user_name and email and pw:
            salt = random_string(8)
            pw += salt
            timestamp = int(time.time())
            sql = "insert into `cms_user` (`user_name`,`email`, `password`, `salt`, `status`, `add_time`, `edit_time`)"
            sql += " values(%s,%s,%s,%s,%s,%s,%s)"
            mdb._ensure_connected()
            return mdb.execute(sql, user_name, email, md5(pw.encode('utf-8')).hexdigest(), salt, status, timestamp,
                               timestamp)
        else:
            return None

    def delete(self, user_id):
        mdb._ensure_connected()
        query = "DELETE FROM `cms_user` WHERE `user_id`=%s"
        mdb.execute(query, user_id)

    def update(self, user_id, user_name='', email=None, pw=None, status=None):
        if user_id:
            timestamp = int(time.time())
            sql = "update `cms_user` set `user_name`= \'%s\'" % user_name
           if email:
                sql += ", `email` = \'%s\'" % email
            if pw:
                salt = random_string(8)
                pw += salt
                sql += ", `password` = \'%s\', `salt` = \'%s\'" % (md5(pw.encode('utf-8')).hexdigest(), salt)
            if status:
                sql += ", `status` = %s" % status
            sql += ", `edit_time` = %s where `user_id` = \'%s\' LIMIT 1" % (timestamp, user_id)
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

    def get_by_name(self, user_name):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_user` WHERE `user_name` = \'%s\' LIMIT 1' % user_name)

    def get_by_email(self, email):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_user` WHERE `email` = \'%s\' LIMIT 1' % email)

    def check_name_email(self, user_name='', email=''):
        sql = "SELECT * FROM `cms_user` WHERE `user_name` = %s and `email` = %s LIMIT 1"
        sdb._ensure_connected()
        user = sdb.get(sql, user_name, email)
        if user:
            return True
        else:
            return False

    def check_user_password(self, user_name='', pw=''):
        if user_name and pw:
            user = self.get_by_name(user_name)
            return user and user.name == user_name and user.password == pw
        else:
            return False

    def check_email_password(self, email='', pw=''):
        if email and pw:
            user = self.get_by_email(email)
            return user and user.email == email and user.password == pw
        else:
            return False

    def get_role(self, user_id):
        sql = "SELECT role_name FROM `cms_role` left join `cms_user_role` " \
              "on `cms_role`.role_id = `cms_user_role`.role_id and user_id = %s"
        sdb._ensure_connected()
        return sdb.query(sql, user_id)


User = User()