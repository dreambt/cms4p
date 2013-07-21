# -*- coding: utf-8 -*-
from core.common import getAttr
from model.articles import post_list_format
from model import mdb, sdb

_author__ = 'baitao.ji'


class Archives():
    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_archive` ORDER BY `archive_name` DESC')

    def get(self, archive_id=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_archive` WHERE `archive_id` = %s' % str(archive_id))

    def get_by_name(self, archive_name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_archive` WHERE `archive_name` = \'%s\'' % archive_name)

    def get_post_num_by_archive_id(self, archive_id=''):
        sql = 'SELECT count(*) FROM `cms_posts` p ' \
              'inner join `cms_archive_post` ap on p.`post_id` = ap.post_id and ap.archive_id = \'%s\''
        sdb._ensure_connected()
        return sdb.get(sql, archive_id)

    def get_post_num_by_archive_name(self, archive_name=''):
        sql = 'SELECT count(*) FROM `cms_posts` p ' \
              'inner join `cms_archive_post` ap on p.`post_id` = ap.post_id ' \
              'inner join `cms_archive` a on ap.`archive_id` = a.archive_id and a.archive_name = \'%s\''
        sdb._ensure_connected()
        return sdb.get(sql, archive_name)

    def get_page_posts_by_archive_name(self, archive_name='', page=1, limit=''):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        sql = "SELECT p.* FROM `cms_posts` p " \
              "inner join `cms_archive_post` ap on p.`post_id` = ap.post_id " \
              "inner join `cms_archive` a on ap.`archive_id` = a.archive_id and a.archive_name = \'%s\''" \
              "ORDER BY `id` DESC LIMIT %s,%s"
        sdb._ensure_connected()
        return post_list_format(sdb.query(sql, archive_name, (int(page) - 1) * limit, limit))

    def add_post_to_archive(self, archive_id='', post_id=''):
        mdb._ensure_connected()
        mdb.execute("INSERT INTO `cms_archive_post` (`archive_id`, `post_id`) values %s",
                    ','.join('(%d,%d)' % (archive_id, x) for x in post_id))
        mdb.execute("UPDATE `cms_archive` SET `post_num` = `post_num`+1 WHERE `archive_id` = %s LIMIT 1", archive_id)

    def add_posts_to_archive(self, archive_id='', post_ids=[]):
        mdb._ensure_connected()
        mdb.execute("INSERT INTO `cms_archive_post` (`archive_id`, `post_id`) values (%s,%s)", archive_id, post_ids)
        mdb.execute("UPDATE `cms_archive` SET `post_num` = `post_num`+%s WHERE `archive_id` = %s LIMIT 1",
                    len(post_ids), archive_id)

    def remove_post_from_archive(self, archive_id='', post_id=''):
        mdb._ensure_connected()
        mdb.execute("DELETE FROM `cms_archive_post` WHERE `archive_id` = %s and `post_id` = %s LIMIT 1", archive_id,
                    post_id)
        mdb.execute("UPDATE `cms_archive` SET `post_num` = `post_num`-1 WHERE `archive_id` = %s LIMIT 1", archive_id)

    def remove_posts_from_archive(self, archive_id='', post_ids=[]):
        mdb._ensure_connected()
        mdb.execute("DELETE FROM `cms_archive_post` WHERE `archive_id` = %s and `post_id` in (%s) LIMIT 1", archive_id,
                    ','.join(post_ids))
        mdb.execute("UPDATE `cms_archive` SET `post_num` = `post_num`-%s WHERE `archive_id` = %s LIMIT 1",
                    len(post_ids), archive_id)


Archives = Archives()