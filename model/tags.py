# -*- coding: utf-8 -*-
from model.articles import post_list_format
from model import mdb, sdb
from setting import EACH_PAGE_POST_NUM, HOT_TAGS_NUM

_author__ = 'baitao.ji'


class Tags():
    def get_all_tag_name(self, limit=HOT_TAGS_NUM):
        #for add/edit post
        sdb._ensure_connected()
        return sdb.query('SELECT `tag_name` FROM `cms_tags` ORDER BY `tag_id` DESC LIMIT %d' % limit)

    def get_all(self, limit=HOT_TAGS_NUM):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_tags` ORDER BY `tag_id` DESC LIMIT %d' % limit)

    def get_hot_tag(self, limit=HOT_TAGS_NUM):
        #for sider
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_tags` ORDER BY `tag_hot` DESC LIMIT %d' % limit)

    def get_tag_by_name(self, tag_name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_tags` WHERE `tag_name` = \'%s\'' % tag_name)

    def get_posts_num_by_tag_name(self, tag_name=''):
        sdb._ensure_connected()
        return sdb.query("SELECT count(*) FROM `cms_posts` WHERE `tags` like \'%s\'" % tag_name)

    def get_page_posts_by_tag_name(self, tag_name='', page=1, limit=EACH_PAGE_POST_NUM):
        page = int(page)
        sdb._ensure_connected()
        return post_list_format(sdb.query(
            "SELECT * FROM `cms_posts` WHERE `tags` like \'%s\' ORDER BY `views` DESC LIMIT %s,%s" % (
                tag_name, (int(page) - 1) * limit, limit)))

Tags = Tags()