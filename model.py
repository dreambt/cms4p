# -*- coding: utf-8 -*-
import random
import re
import time
from hashlib import md5
from datetime import datetime, timedelta

from tornado import database

from common import slugfy, time_from_now, cnnow, timestamp_to_datetime, safe_encode, getAttr
from setting import *


##
HTML_REG = re.compile(r"""<[^>]+>""", re.I | re.M | re.S)
CODE_RE = re.compile(r"""\[code\](.+?)\[/code\]""", re.I | re.M | re.S)

#主数据库 进行Create,Update,Delete 操作
#从数据库 读取
mdb = database.Connection("%s:%s" % (MYSQL_HOST_M, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=MAX_IDLE_TIME)
sdb = database.Connection("%s:%s" % (MYSQL_HOST_S, str(MYSQL_PORT)), MYSQL_DB, MYSQL_USER, MYSQL_PASS,
                          max_idle_time=MAX_IDLE_TIME)


def n2br(text):
    con = text.replace('>\n\n', '>').replace('>\n', '>')
    con = "<p>%s</p>" % ('</p><p>'.join(con.split('\n\n')))
    return '<br/>'.join(con.split("\n"))


def tran_content(text, code=False):
    if code:
        codetag = '[mycodeplace]'
        codes = CODE_RE.findall(text)
        for i in range(len(codes)):
            text = text.replace(codes[i], codetag)
        text = text.replace("[code]", "").replace("[/code]", "")

        text = n2br(text)

        a = text.split(codetag)
        b = []
        for i in range(len(a)):
            b.append(a[i])
            try:
                b.append('<pre><code>' + safe_encode(codes[i]) + '</code></pre>')
            except:
                pass

        return ''.join(b)
    else:
        return n2br(text)


def post_list_format(posts):
    for obj in posts:
        obj.absolute_url = '%s/topic/%d/%s' % (BASE_URL, obj.id, slugfy(obj.title))
        obj.taglist = ', '.join(
            ["""<a href="%s/tag/%s/" rel="tag">%s</a>""" % (BASE_URL, tag, tag) for tag in obj.tags.split(',')])

        if '<!--more-->' in obj.content:
            obj.shorten_content = obj.content.split('<!--more-->')[0]
        else:
            obj.shorten_content = HTML_REG.sub('', obj.content[:int(getAttr('SHORTEN_CONTENT_WORDS'))])

        obj.add_time_fn = time_from_now(int(obj.add_time))
    return posts


def post_detail_formate(obj):
    if obj:
        slug = slugfy(obj.title)
        obj.slug = slug
        obj.absolute_url = '%s/topic/%d/%s' % (BASE_URL, obj.id, slug)
        obj.shorten_url = '%s/t/%s' % (BASE_URL, obj.id)
        if '[/code]' in obj.content:
            obj.highlight = True
        else:
            obj.highlight = False
        obj.content = tran_content(obj.content, obj.highlight)
        obj.taglist = ', '.join(
            ["""<a href="%s/tag/%s/" rel="tag">%s</a>""" % (BASE_URL, tag, tag) for tag in obj.tags.split(',')])
        obj.add_time_fn = time_from_now(int(obj.add_time))
        obj.last_modified = timestamp_to_datetime(obj.edit_time)
        obj.keywords = obj.tags
        obj.description = HTML_REG.sub('', obj.content[:DESCRIPTION_CUT_WORDS])
        #get prev and next obj
        obj.prev_obj = sdb.get('SELECT `id`,`title` FROM `sp_posts` WHERE `id` > %s LIMIT 1' % str(obj.id))
        if obj.prev_obj:
            obj.prev_obj.slug = slugfy(obj.prev_obj.title)
        obj.next_obj = sdb.get(
            'SELECT `id`,`title` FROM `sp_posts` WHERE `id` < %s ORDER BY `id` DESC LIMIT 1' % str(obj.id))
        if obj.next_obj:
            obj.next_obj.slug = slugfy(obj.next_obj.title)
            #get relative obj base tags
        obj.relative = []
        if obj.tags:
            idlist = []
            getit = False
            for tag in obj.tags.split(','):
                tagobj = Tag.get_tag_by_name(tag)
                if tagobj and tagobj.content:
                    pids = tagobj.content.split(',')
                    for pid in pids:
                        if pid != str(obj.id) and pid not in idlist:
                            idlist.append(pid)
                            if len(idlist) >= RELATIVE_POST_NUM:
                                getit = True
                                break
                if getit:
                    break
                    #
            if idlist:
                obj.relative = sdb.query('SELECT `id`,`title` FROM `sp_posts` WHERE `id` in(%s) LIMIT %s' % (
                    ','.join(idlist), str(len(idlist))))
                if obj.relative:
                    for robj in obj.relative:
                        robj.slug = slugfy(robj.title)
                        #get comment
        obj.coms = []
        if obj.comment_num > 0:
            if obj.comment_num >= EACH_PAGE_COMMENT_NUM:
                first_limit = EACH_PAGE_COMMENT_NUM
            else:
                first_limit = obj.comment_num
            obj.coms = Comment.get_post_page_comments_by_id(obj.id, 0, first_limit)
    return obj


def comment_format(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
        obj.add_time = time_from_now(int(obj.add_time))

        if obj.visible:
            obj.short_content = HTML_REG.sub('', obj.content[:RECENT_COMMENT_CUT_WORDS])
        else:
            obj.short_content = 'Your comment is awaiting moderation.'[:RECENT_COMMENT_CUT_WORDS]

        obj.content = obj.content.replace('\n', '<br/>')
    return objs


def comment_format_admin(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
        obj.content = obj.content.replace('\n', '<br/>')
    return objs


def user_format(objs):
    for obj in objs:
        obj.gravatar = 'http://www.gravatar.com/avatar/%s' % md5(obj.email).hexdigest()
    return objs

###以下是各个数据表的操作


class Article():
    def count_all(self, cat=None, title=None):
        sdb._ensure_connected()
        sql = "SELECT COUNT(*) AS num FROM `sp_posts` WHERE 1=1"
        if cat:
            sql += " and category = \'%s\'" % cat
        if title:
            sql += " and title like \'%s\'" % title
        return sdb.query(sql)[0]['num']

    def create_article(self, params):
        query = "INSERT INTO `sp_posts` (`category`,`title`,`content`,`closecomment`,`tags`,`password`,`add_time`,`edit_time`,`archive`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'],
                           params['tags'], params['password'], params['add_time'], params['edit_time'],
                           params['archive'])

    def update_post_edit(self, params):
        query = "UPDATE `sp_posts` SET `category` = %s, `title` = %s, `content` = %s, `closecomment` = %s, `tags` = %s, `password` = %s, `edit_time` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'],
                    params['tags'], params['password'], params['edit_time'], params['id'])
        ### update 返回不了 lastrowid，直接返回 post id
        return params['id']

    def update_post_edit_author(self, userid, author):
        sql = "UPDATE `sp_posts` SET `author` = %s WHERE `id` = %s LIMIT 1" % (author, userid)
        mdb._ensure_connected()
        mdb.execute(sql)

    def update_comment_num(self, num=1, userid=''):
        query = "UPDATE `sp_posts` SET `comment_num` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        return mdb.execute(query, num, userid)

    def delete_post(self, userid=''):
        if userid:
            obj = self.get_article_simple(userid)
            if obj:
                limit = obj.comment_num
                mdb._ensure_connected()
                mdb.execute("DELETE FROM `sp_posts` WHERE `id` = %s LIMIT 1", userid)
                mdb.execute("DELETE FROM `sp_comments` WHERE `postid` = %s LIMIT %s", userid, limit)

    def get_article(self, userid):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_posts` WHERE `id` = %s' % str(userid))

    def get_all(self):
        sdb._ensure_connected()
        return post_list_format(sdb.query("SELECT * FROM `sp_posts` ORDER BY `id` DESC"))

    # 分页
    def get_paged(self, page=1, limit=None, cat=None, title=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `sp_posts` where 1=1"
        if cat:
            sql += " and category = \'%s\'" % cat
        if title:
            sql += " and title like \'%s\'" % title
        sql += " ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    '''获取指定用户发表的所有文章'''
    def get_article_by_author(self, author):
        sql = "SELECT * FROM `sp_posts` where `author` = '%s'" % author
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_max_id(self):
        sdb._ensure_connected()
        maxobj = sdb.query("select max(id) as maxid from `sp_posts`")
        return str(maxobj[0]['maxid'])

    def get_last_post_add_time(self):
        sdb._ensure_connected()
        obj = sdb.get('SELECT `add_time` FROM `sp_posts` ORDER BY `id` DESC')
        if obj:
            return datetime.fromtimestamp(obj.add_time)
        else:
            return datetime.utcnow() + timedelta(hours=+ 8)

    def get_last_post(self, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        sdb._ensure_connected()
        return post_list_format(
            sdb.query("SELECT * FROM `sp_posts` ORDER BY `id` DESC LIMIT %s" % limit))

    def get_article_detail(self, userid):
        sdb._ensure_connected()
        return post_detail_formate(sdb.get('SELECT * FROM `sp_posts` WHERE `id` = %s LIMIT 1' % str(userid)))

    def get_article_simple(self, userid):
        sdb._ensure_connected()
        return sdb.get(
            'SELECT `id`,`category`,`title`,`comment_num`,`closecomment`,`password` FROM `sp_posts` WHERE `id` = %s' % str(
                userid))

    def get_post_for_sitemap(self, ids=[]):
        sdb._ensure_connected()
        return sdb.query("SELECT `id`,`edit_time` FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
            ','.join(ids), str(len(ids))))


Article = Article()


class Comment():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `sp_comments`')[0]['num']

    def create_comment(self, params):
        query = "INSERT INTO `sp_comments` (`postid`,`author`,`email`,`url`,`visible`,`add_time`,`content`) values(%s,%s,%s,%s,%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['postid'], params['author'], params['email'], params['url'], params['visible'],
                           params['add_time'], params['content'])

    def update_comment(self, params):
        query = "UPDATE `sp_comments` SET `author` = %s, `email` = %s, `url` = %s, `visible` = %s, `content` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['author'], params['email'], params['url'], params['visible'], params['content'],
                    params['id'])
        ### update 返回不了 lastrowid，直接返回 id
        return params['id']

    def delete_comment(self, id):
        cobj = self.get_comment(id)
        postid = cobj.postid
        pobj = Article.get_article(postid)

        mdb._ensure_connected()
        mdb.execute("DELETE FROM `sp_comments` WHERE `id` = %s LIMIT 1", id)
        if pobj:
            Article.update_comment_num(pobj.comment_num - 1, postid)
        return

    def get_comment(self, id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_comments` WHERE `id` = %s' % str(id))

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_COMMENT_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `sp_comments` ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return comment_format_admin(sdb.query(sql))

    def get_recent_comments(self, limit=None):
        if limit is None:
            limit = getAttr('RECENT_COMMENT_NUM')
        sdb._ensure_connected()
        return comment_format(sdb.query('SELECT * FROM `sp_comments` ORDER BY `id` DESC LIMIT %s' % limit))

    def get_post_page_comments_by_id(self, postid=0, min_comment_id=0, limit=EACH_PAGE_COMMENT_NUM):
        if min_comment_id == 0:
            sdb._ensure_connected()
            return comment_format(sdb.query(
                'SELECT * FROM `sp_comments` WHERE `postid`= %s ORDER BY `id` DESC LIMIT %s' % (
                    str(postid), str(limit))))
        else:
            sdb._ensure_connected()
            return comment_format(sdb.query(
                'SELECT * FROM `sp_comments` WHERE `postid`= %s AND `id` < %s ORDER BY `id` DESC LIMIT %s' % (
                    str(postid), str(min_comment_id), str(limit))))


Comment = Comment()


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


class Category():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `sp_category`')[0]['num']

    def create_category(self, params):
        mdb._ensure_connected()
        query = "INSERT INTO `sp_category` (`name`,`showtype`,`displayorder`,`id_num`,`content`) values(%s,%s,%s,1,'')"
        mdb.execute(query, params['name'], params['showtype'], params['displayorder'])

    def update_cat(self, params):
        mdb._ensure_connected()
        query = "UPDATE `sp_category` SET `name`=%s, `showtype`=%s, `displayorder`=%s WHERE ID=%s"
        mdb.execute(query, params['name'], params['showtype'], params['displayorder'], params['id'])

    def delete_category(self, id):
        mdb._ensure_connected()
        query = "DELETE FROM `sp_category` WHERE `id`=%s"
        mdb.execute(query, id)

    def get_category(self, id=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_category` WHERE `id` = %s' % str(id))

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `sp_category` ORDER BY `id` DESC')

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_CATEGORY_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `sp_category` ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_paged_posts_by_name(self, name='', page=1, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        obj = self.get_by_name(name)
        if obj:
            page = int(page)
            limit = int(limit)
            idlist = obj.content.split(',')
            getids = idlist[limit * (page - 1):limit * page]
            sdb._ensure_connected()
            return post_list_format(sdb.query(
                "SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), str(len(getids)))))
        else:
            return []

    def get_all_cat_name(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `sp_category` WHERE id > 0 ORDER BY `id` DESC')

    def get_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\'' % name)

    def get_all_post_num(self, name=''):
        obj = self.get_by_name(name)
        if obj and obj.content:
            return len(obj.content.split(','))
        else:
            return 0

    def add_postid_to_cat(self, name='', postid=''):
        mdb._ensure_connected()
        # 因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
        obj = mdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\'' % name)

        if obj:
            query = "UPDATE `sp_category` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
            mdb.execute(query, "%s," % postid, obj.id)
        else:
            query = "INSERT INTO `sp_category` (`name`,`id_num`,`content`) values(%s,1,%s)"
            mdb.execute(query, name, postid)

    def remove_postid_from_cat(self, name='', postid=''):
        mdb._ensure_connected()
        if name:
            obj = mdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\'' % name)
            if obj:
                idlist = obj.content.split(',')
                if postid in idlist:
                    idlist.remove(postid)
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist) == 0:
                        mdb.execute("DELETE FROM `sp_category` WHERE `id` = %s LIMIT 1", str(obj.id))
                    else:
                        query = "UPDATE `sp_category` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                        mdb.execute(query, len(idlist), ','.join(idlist), str(obj.id))
                else:
                    pass
            else:
                print 'not obj'
        else:
            print 'not name'

    def get_sitemap_by_id(self, id=''):
        obj = self.get_category(id)
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


class Tag():
    def get_all_tag_name(self):
        #for add/edit post
        sdb._ensure_connected()
        return sdb.query('SELECT `name` FROM `sp_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `sp_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_hot_tag_name(self):
        #for sider
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `sp_tags` ORDER BY `id_num` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_tag_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\'' % name)

    def get_all_post_num(self, name=''):
        obj = self.get_tag_by_name(name)
        if obj and obj.content:
            return len(obj.content.split(','))
        else:
            return 0

    def get_tag_page_posts(self, name='', page=1, limit=EACH_PAGE_POST_NUM):
        obj = self.get_tag_by_name(name)
        if obj and obj.content:
            page = int(page)
            idlist = obj.content.split(',')
            getids = idlist[limit * (page - 1):limit * page]
            sdb._ensure_connected()
            return post_list_format(sdb.query(
                "SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), len(getids))))
        else:
            return []

    def add_postid_to_tags(self, tags=[], postid=''):
        mdb._ensure_connected()
        for tag in tags:
            obj = mdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\'' % tag)

            if obj:
                query = "UPDATE `sp_tags` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
                mdb.execute(query, "%s," % postid, obj.id)
            else:
                query = "INSERT INTO `sp_tags` (`name`,`id_num`,`content`) values(%s,1,%s)"
                mdb.execute(query, tag, postid)

    def remove_postid_from_tags(self, tags=[], postid=''):
        mdb._ensure_connected()
        for tag in tags:
            obj = mdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\'' % tag)

            if obj:
                idlist = obj.content.split(',')
                if postid in idlist:
                    idlist.remove(postid)
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist) == 0:
                        mdb.execute("DELETE FROM `sp_tags` WHERE `id` = %s LIMIT 1", obj.id)
                    else:
                        query = "UPDATE `sp_tags` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                        mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
                else:
                    pass


Tag = Tag()


class Archive():
    def get_latest_archive_name(self):
        sdb._ensure_connected()
        objs = sdb.get('SELECT `name` FROM `sp_archive` ORDER BY `name` DESC')
        print objs[0].name
        return objs[0].name

    def get_all_archive_name(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `sp_archive` ORDER BY `name` DESC')

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `sp_archive` ORDER BY `name` DESC')

    def get_all_archive_id(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `id` FROM `sp_archive` ORDER BY `id` DESC')

    def get_archive_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\'' % name)

    def get_all_post_num(self, name=''):
        obj = self.get_archive_by_name(name)
        if obj and obj.content:
            return len(obj.content.split(','))
        else:
            return 0

    def get_archive_page_posts(self, name='', page=1, limit=EACH_PAGE_POST_NUM):
        obj = self.get_archive_by_name(name)
        if obj:
            page = int(page)
            idlist = obj.content.split(',')
            getids = idlist[limit * (page - 1):limit * page]
            sdb._ensure_connected()
            return post_list_format(sdb.query(
                "SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), str(len(getids)))))
        else:
            return []

    def add_postid_to_archive(self, name='', postid=''):
        mdb._ensure_connected()
        #因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
        obj = mdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\'' % name)

        if obj:
            query = "UPDATE `sp_archive` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
            mdb.execute(query, "%s," % postid, obj.id)
        else:
            query = "INSERT INTO `sp_archive` (`name`,`id_num`,`content`) values(%s,1,%s)"
            mdb.execute(query, name, postid)

    def remove_postid_from_archive(self, name='', postid=''):
        mdb._ensure_connected()
        obj = mdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\'' % name)
        if obj:
            idlist = obj.content.split(',')
            if postid in idlist:
                idlist.remove(postid)
                try:
                    idlist.remove('')
                except:
                    pass
                if len(idlist) == 0:
                    mdb.execute("DELETE FROM `sp_archive` WHERE `id` = %s LIMIT 1", obj.id)
                else:
                    query = "UPDATE `sp_archive` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                    mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
            else:
                pass

    def get_archive(self, id=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `sp_archive` WHERE `id` = %s' % str(id))


Archive = Archive()


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


class MyData():
    def flush_all_data(self):
        sql = """
        TRUNCATE TABLE `sp_category`;
        TRUNCATE TABLE `sp_comments`;
        TRUNCATE TABLE `sp_links`;
        TRUNCATE TABLE `sp_posts`;
        TRUNCATE TABLE `sp_tags`;
        TRUNCATE TABLE `sp_archive`;
        TRUNCATE TABLE `sp_user`;
        TRUNCATE TABLE `sp_role`;
        TRUNCATE TABLE `sp_user_role`;
        """
        mdb._ensure_connected()
        mdb.execute(sql)

    def creat_table(self):
        sql = """
DROP TABLE IF EXISTS `sp_category`;
CREATE TABLE IF NOT EXISTS `sp_category` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `showtype` varchar(7) NOT NULL DEFAULT 'default',
  `displayorder` tinyint(3) NOT NULL DEFAULT '0',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_archive`;
CREATE TABLE IF NOT EXISTS `sp_archive` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_comments`;
CREATE TABLE IF NOT EXISTS `sp_comments` (
  `id` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `postid` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `author` varchar(20) NOT NULL,
  `email` varchar(30) NOT NULL,
  `url` varchar(75) NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `add_time` int(10) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `postid` (`postid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_links`;
CREATE TABLE IF NOT EXISTS `sp_links` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `displayorder` tinyint(3) NOT NULL DEFAULT '0',
  `name` varchar(100) NOT NULL DEFAULT '',
  `url` varchar(200) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_posts`;
CREATE TABLE IF NOT EXISTS `sp_posts` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(17) NOT NULL DEFAULT '',
  `title` varchar(100) NOT NULL DEFAULT '',
  `author` varchar(20) NOT NULL DEFAULT '',
  `content` mediumtext NOT NULL,
  `comment_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `closecomment` tinyint(1) NOT NULL DEFAULT '0',
  `tags` varchar(100) NOT NULL,
  `archive` varchar(6) NOT NULL DEFAULT '209901',
  `password` varchar(16) NOT NULL DEFAULT '',
  `add_time` int(10) unsigned NOT NULL DEFAULT '0',
  `edit_time` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `category` (`category`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_tags`;
CREATE TABLE IF NOT EXISTS `sp_tags` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `id_num` (`id_num`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_user`;
CREATE TABLE IF NOT EXISTS `sp_user` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL DEFAULT '',
  `email` varchar(40) NOT NULL DEFAULT '',
  `password` varchar(32) NOT NULL DEFAULT '',
  `salt` varchar(8) NOT NULL DEFAULT '',
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `add_time` int(10) unsigned NOT NULL DEFAULT '0',
  `edit_time` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

"""
        mdb._ensure_connected()
        mdb.execute(sql)

MyData = MyData()
