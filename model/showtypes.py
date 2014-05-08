# -*- coding: utf-8 -*-
from model import sdb, mdb
from setting import LINK_NUM

_author__ = 'baitao.ji'


class ShowTypes():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_show_types`')[0]['num']

    def create(self, params):
        query = "INSERT INTO `cms_show_types` (`type_key`, `type_name`) values(%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['type_key'], params['type_name'])

    def update(self, params):
        query = "UPDATE `cms_show_types` SET `type_name` = %s WHERE `type_key` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['type_name'], params['type_key'])

    def delete(self, type_key):
        mdb._ensure_connected()
        mdb.execute("DELETE FROM `cms_show_types` WHERE `type_key` = %s LIMIT 1", type_key)

    def get(self, type_key):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_show_types` WHERE `type_key` = %s' % str(type_key))

    def get_all(self, limit=LINK_NUM):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_show_types` LIMIT %s' % str(limit))


ShowTypes = ShowTypes()