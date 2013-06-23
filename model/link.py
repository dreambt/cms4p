# -*- coding: utf-8 -*-
from core.common import getAttr
from model.base import sdb, mdb
from setting import LINK_NUM

_author__ = 'baitao.ji'


class Link():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `sp_links`')[0]['num']

    def create_link(self, params):
        query = "INSERT INTO `sp_links` (`displayorder`,`name`,`url`) values(%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['displayorder'], params['name'], params['url'])

    def update_link(self, params):
        query = "UPDATE `sp_links` SET `displayorder` = %s, `name` = %s, `url` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['displayorder'], params['name'], params['url'], params['id'])

    def delete_link(self, id):
        mdb._ensure_connected()
        mdb.execute("DELETE FROM `sp_links` WHERE `id` = %s LIMIT 1", id)

    def get_link(self, id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_links` WHERE `id` = %s' % str(id))

    def get_all_links(self, limit=LINK_NUM):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `sp_links` ORDER BY `displayorder` DESC LIMIT %s' % str(limit))

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_LINK_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `sp_links` ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return sdb.query(sql)


Link = Link()