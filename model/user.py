# -*- coding: utf-8 -*-
import random
import time
from hashlib import md5
from core.common import getAttr
from model.base import sdb, mdb

_author__ = 'baitao.ji'


def user_format(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
    return objs


class User():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `sp_user`')[0]['num']

    def create_user(self, name='', email='', pw='', status=1):
        if name and email and pw:
            salt = ''.join(random.sample('zAyBxCwDvEuFtGsHrIqJpKoLnMmNlOkPjQiRhSgTfUeVdWcXbYaZ1928374650', 8))
            pw += salt
            timestamp = int(time.time())
            sql = "insert into `sp_user` (`name`,`email`, `password`, `salt`, `status`, `add_time`, `edit_time`)"
            sql += " values(%s,%s,%s,%s,%s,%s,%s)"
            mdb._ensure_connected()
            return mdb.execute(sql, name, email, md5(pw.encode('utf-8')).hexdigest(), salt, status, timestamp, timestamp)
        else:
            return None

    def delete_user(self, id):
        mdb._ensure_connected()
        query = "DELETE FROM `sp_user` WHERE `id`=%s"
        mdb.execute(query, id)

    def update_user(self, name='', email=None, pw=None, status=None):
        if name:
            timestamp = int(time.time())
            sql = "update `sp_user` set `name`= \'%s\'" % name
            if email is not None:
                sql += ", `email` = \'%s\'" % email
            if pw is not None:
                salt = ''.join(random.sample('zAyBxCwDvEuFtGsHrIqJpKoLnMmNlOkPjQiRhSgTfUeVdWcXbYaZ1928374650', 8))
                pw += salt
                sql += ", `password` = \'%s\', `salt` = \'%s\'" % (md5(pw.encode('utf-8')).hexdigest(), salt)
            if status is not None:
                sql += ", `status` = %s" % status
            sql += ", `edit_time` = %s where `name` = \'%s\' LIMIT 1" % (timestamp, name)
            mdb._ensure_connected()
            return mdb.execute(sql)
        else:
            return None

    def update_user_audit(self, id, status=''):
        sql = "update `sp_user` set `status` = %s where `id` = %s LIMIT 1"
        mdb._ensure_connected()
        return mdb.execute(sql, status, id)

    def get_user(self, id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_user` WHERE `id` = %s' % id)

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `sp_user`')

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_USER_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `sp_user` ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return user_format(sdb.query(sql))

    def check_has_user(self):
        sdb._ensure_connected()
        return sdb.get('SELECT `id` FROM `sp_user`')

    def get_user_by_name(self, name):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_user` WHERE `name` = \'%s\'' % name)

    def get_user_by_email(self, email):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_user` WHERE `email` = \'%s\'' % email)

    def check_name_email(self, name='', email=''):
        sql = "SELECT * FROM `sp_user` WHERE `name` = %s and `email` = %s"
        sdb._ensure_connected()
        user = sdb.get(sql, name, email)
        if user:
            return True
        else:
            return False

    def check_user_password(self, name='', pw=''):
        if name and pw:
            user = self.get_user_by_name(name)
            return user and user.name == name and user.password == pw
        else:
            return False

    def check_email_password(self, email='', pw=''):
        if email and pw:
            user = self.get_user_by_email(email)
            return user and user.email == email and user.password == pw
        else:
            return False


User = User()