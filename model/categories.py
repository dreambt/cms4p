# -*- coding: utf-8 -*-
import tornado.web
from core.common import cnnow, timestamp_to_datetime, getAttr
from model.posts import post_list_format
from model import sdb, mdb
from setting import BASE_URL

_author__ = 'baitao.ji'


class Categories():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_category`')[0]['num']

    def create(self, params):
        mdb._ensure_connected()
        query = "INSERT INTO `cms_category` (`father_category_id`, `category_name`, `display_order`, `show_type`, " \
                "`description`, `allow_comment`, `allow_publish`) values(%s,%s,%s,%s,%s,%s,%s,%s)"
        mdb.execute(query, params['father_category_id'], params['category_name'], params['display_order'],
                    params['show_type'], params['description'], params['allow_comment'], params['allow_publish'])

    def update(self, params):
        mdb._ensure_connected()
        sql = "UPDATE `cms_category` SET "
        if params['father_category_id']:
            sql += "`father_category_id` = %s," % params['father_category_id']
        sql += "`category_name` = \'%s\'," % params['category_name']
        sql += "`display_order` = %s," % params['display_order']
        sql += "`show_type` = \'%s\'," % params['show_type']
        sql += "`description` = \'%s\'," % params['description']
        sql += "`allow_comment` = %s," % params['allow_comment']
        sql += "`allow_publish` = %s," % params['allow_publish']
        sql += "category_id = %s WHERE category_id = %s"
        mdb.execute(sql, params['category_id'], params['category_id'])

    def delete(self, category_id):
        mdb._ensure_connected()
        query = "DELETE FROM `cms_category` WHERE `category_id` = %s"
        mdb.execute(query, category_id)

    def delete_by_father_category_id(self, father_category_id):
        mdb._ensure_connected()
        query = "DELETE FROM `cms_category` WHERE `father_category_id` = %s"
        mdb.execute(query, father_category_id)

    def get(self, category_id):
        if category_id is None:
            raise tornado.web.HTTPError(404)
        sdb._ensure_connected()
        post = sdb.get('SELECT * FROM `cms_category` WHERE `category_id` = %s' % category_id)
        if post is None:
            raise tornado.web.HTTPError(404)
        return post

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_category` ORDER BY `father_category_id` ASC, `display_order` DESC')

    def get_all_kv(self, father_category_id=None):
        if father_category_id:
            sql = "SELECT `category_id`,`category_name` FROM `cms_category` WHERE `father_category_id` = 0 " \
                  "ORDER BY `father_category_id` ASC, `display_order` DESC"
        else:
            sql = "SELECT `category_id`,`category_name` FROM `cms_category` WHERE `show_type` <> \'url\' " \
                  "ORDER BY `father_category_id` ASC, `display_order` DESC"
        sdb._ensure_connected()
        return sdb.query(sql)

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_CATEGORY_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `cms_category` ORDER BY `father_category_id` ASC, `display_order` DESC LIMIT %s,%s" % (
            (int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_posts_by_category_id(self, category_id='', page=1, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `cms_posts` WHERE `category_id` = %s ORDER BY `post_id` DESC LIMIT %s,%s" % (
            category_id, (int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return post_list_format(sdb.query(sql))

    def get_post_num_by_category_id(self, category_id=''):
        sql = "SELECT count(*) FROM `cms_posts` WHERE `category_id` = %s" % category_id
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_all_category_name(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `category_id`, `category_name` FROM `cms_category`')

    def get_by_category_name(self, category_name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_category` WHERE `category_name` like \'%s\'' % category_name)

    def get_sitemap_by_category_id(self, category_id=''):
        obj = self.get(category_id)
        if not obj:
            return ''
        if not obj.content:
            return ''

        urlstr = """<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n """
        urllist = []
        urllist.append('<?xml version="1.0" encoding="UTF-8"?>\n')
        urllist.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        urllist.append(
            urlstr % ( "%s/c/%s" % (BASE_URL, str(obj.id)), cnnow().strftime("%Y-%m-%dT%H:%M:%SZ"), 'daily', '0.8'))

        from model.posts import Posts

        objs = Posts.get_post_for_sitemap(obj.content.split(','))
        for p in objs:
            if p:
                urllist.append(urlstr % (
                    "%s/t/%s" % (BASE_URL, str(p.id)),
                    timestamp_to_datetime(p.edit_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    'weekly', '0.6'))

        urllist.append('</urlset>')
        return ''.join(urllist)


Categories = Categories()