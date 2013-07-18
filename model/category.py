# -*- coding: utf-8 -*-
from core.common import cnnow, timestamp_to_datetime, getAttr
from model.article import post_list_format
from model.base import sdb, mdb
from setting import BASE_URL

_author__ = 'baitao.ji'


class Category():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_category`')[0]['num']

    def create(self, params):
        mdb._ensure_connected()
        query = "INSERT INTO `cms_category` (`name`,`showtype`,`displayorder`,`id_num`,`content`) values(%s,%s,%s,0,'')"
        mdb.execute(query, params['name'], params['showtype'], params['displayorder'])

    def update(self, params):
        mdb._ensure_connected()
        query = "UPDATE `cms_category` SET `name`=%s, `showtype`=%s, `displayorder`=%s WHERE ID=%s"
        mdb.execute(query, params['name'], params['showtype'], params['displayorder'], params['id'])

    def delete(self, id):
        mdb._ensure_connected()
        query = "DELETE FROM `cms_category` WHERE `id` = %s"
        mdb.execute(query, id)

    def get(self, id=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_category` WHERE `id` = %s' % str(id))

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_category` ORDER BY `displayorder` DESC')

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_CATEGORY_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `cms_category` ORDER BY `displayorder` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_posts_by_catid(self, catid='', page=1, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        obj = self.get_by_name(name)
        idlist = obj.content.split(',')
        page = int(page)
        limit = int(limit)
        getids = idlist[limit * (page - 1):limit * page]
        if len(getids) > 1:
            sdb._ensure_connected()
            return post_list_format(sdb.query(
                "SELECT * FROM `cms_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), str(len(getids)))))
        else:
            return []

    def get_posts_by_name(self, name='', page=1, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        obj = self.get_by_name(name)
        idlist = obj.content.split(',')
        page = int(page)
        limit = int(limit)
        getids = idlist[limit * (page - 1):limit * page]
        if len(getids) > 1:
            sdb._ensure_connected()
            return post_list_format(sdb.query(
                "SELECT * FROM `cms_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), str(len(getids)))))
        else:
            return []

    def get_all_cat_name(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `cms_category` WHERE id > 0 ORDER BY `id` DESC')

    def get_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_category` WHERE `name` = \'%s\'' % name)

    def get_all_post_num(self, name=''):
        obj = self.get_by_name(name)
        if obj and obj.content:
            return len(obj.content.split(','))
        else:
            return 0

    def add_postid_to_cat(self, name='', postid=''):
        mdb._ensure_connected()
        # 因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
        obj = mdb.get('SELECT * FROM `cms_category` WHERE `name` = \'%s\'' % name)

        if obj:
            query = "UPDATE `cms_category` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
            mdb.execute(query, "%s," % postid, obj.id)
        else:
            query = "INSERT INTO `cms_category` (`name`,`id_num`,`content`) values(%s,1,%s)"
            mdb.execute(query, name, postid)

    def remove_postid_from_cat(self, name='', postid=''):
        mdb._ensure_connected()
        if name:
            obj = mdb.get('SELECT * FROM `cms_category` WHERE `name` = \'%s\'' % name)
            if obj:
                idlist = obj.content.split(',')
                if postid in idlist:
                    idlist.remove(postid)
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist) == 0:
                        mdb.execute("DELETE FROM `cms_category` WHERE `id` = %s LIMIT 1", str(obj.id))
                    else:
                        query = "UPDATE `cms_category` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                        mdb.execute(query, len(idlist), ','.join(idlist), str(obj.id))
                else:
                    pass
            else:
                print 'not obj'
        else:
            print 'not name'

    def get_sitemap_by_id(self, id=''):
        obj = self.get(id)
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

        from model.article import Article

        objs = Article.get_post_for_sitemap(obj.content.split(','))
        for p in objs:
            if p:
                urllist.append(urlstr % (
                    "%s/t/%s" % (BASE_URL, str(p.id)),
                    timestamp_to_datetime(p.edit_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    'weekly', '0.6'))

        urllist.append('</urlset>')
        return ''.join(urllist)


Category = Category()