# -*- coding: utf-8 -*-
from core.common import getAttr
from model import sdb, mdb
from setting import LINK_NUM

_author__ = 'baitao.ji'


class Links():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_links`')[0]['num']

    def create(self, params):
        query = "INSERT INTO `cms_links` (`link_name`, `url`, `display_order`) values(%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['link_name'], params['url'], params['display_order'])

    def update(self, params):
        query = "UPDATE `cms_links` SET `link_name` = \'%s\', `url` = \'%s\', `display_order` = %s " \
                "WHERE `link_id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['link_name'], params['url'], params['display_order'], params['link_id'])

    def delete(self, link_id):
        mdb._ensure_connected()
        mdb.execute("DELETE FROM `cms_links` WHERE `link_id` = %s LIMIT 1", link_id)

    def get(self, link_id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_links` WHERE `link_id` = %s' % str(link_id))

    def get_all(self, limit=LINK_NUM):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_links` ORDER BY `display_order` DESC LIMIT %s' % str(limit))

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_LINK_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `cms_links` ORDER BY `display_order` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return sdb.query(sql)


Links = Links()