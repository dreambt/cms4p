# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from core.common import getAttr, slugfy, time_from_now, timestamp_to_datetime
from model.base import sdb, mdb, HTML_REG, tran_content
from setting import EACH_PAGE_COMMENT_NUM, RELATIVE_POST_NUM, BASE_URL, DESCRIPTION_CUT_WORDS

_author__ = 'baitao.ji'


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
        obj.prev_obj = sdb.get('SELECT `id`,`title` FROM `cms_posts` WHERE `id` > %s LIMIT 1' % str(obj.id))
        if obj.prev_obj:
            obj.prev_obj.slug = slugfy(obj.prev_obj.title)
        obj.next_obj = sdb.get(
            'SELECT `id`,`title` FROM `cms_posts` WHERE `id` < %s ORDER BY `id` DESC LIMIT 1' % str(obj.id))
        if obj.next_obj:
            obj.next_obj.slug = slugfy(obj.next_obj.title)
            #get relative obj base tags
        obj.relative = []
        if obj.tags:
            idlist = []
            getit = False
            for tag in obj.tags.split(','):
                from model.tag import Tag
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
                obj.relative = sdb.query('SELECT `id`,`title` FROM `cms_posts` WHERE `id` in(%s) LIMIT %s' % (
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
            from model.comment import Comment
            obj.coms = Comment.get_post_page_comments_by_id(obj.id, 0, first_limit)
    return obj


class Article():
    def count_all(self, cat=None, title=None):
        sdb._ensure_connected()
        sql = "SELECT COUNT(*) AS num FROM `cms_posts` WHERE 1=1"
        if cat:
            sql += " and category = \'%s\'" % cat
        if title:
            sql += " and title like \'%s\'" % title
        return sdb.query(sql)[0]['num']

    def create(self, params):
        query = "INSERT INTO `cms_posts` (`category`,`title`,`content`,`closecomment`,`tags`,`password`," \
                "`add_time`,`edit_time`,`archive`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'],
                           params['tags'], params['password'], params['add_time'], params['edit_time'],
                           params['archive'])

    def update(self, params):
        query = "UPDATE `cms_posts` SET `category` = %s, `title` = %s, `content` = %s, `closecomment` = %s, " \
                "`tags` = %s, `password` = %s, `edit_time` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'],
                    params['tags'], params['password'], params['edit_time'], params['id'])
        ### update 返回不了 lastrowid，直接返回 post id
        return params['id']

    def update_post_edit_author(self, userid, author):
        sql = "UPDATE `cms_posts` SET `author` = %s WHERE `id` = %s LIMIT 1" % (author, userid)
        mdb._ensure_connected()
        mdb.execute(sql)

    def update_comment_num(self, num=1, userid=''):
        query = "UPDATE `cms_posts` SET `comment_num` = %s WHERE `id` = %s LIMIT 1"
        mdb._ensure_connected()
        return mdb.execute(query, num, userid)

    def delete(self, userid=''):
        if userid:
            obj = self.get_article_simple(userid)
            if obj:
                limit = obj.comment_num
                mdb._ensure_connected()
                mdb.execute("DELETE FROM `cms_posts` WHERE `id` = %s LIMIT 1", userid)
                mdb.execute("DELETE FROM `cms_comments` WHERE `postid` = %s LIMIT %s", userid, limit)

    def get(self, article_id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_posts` WHERE `id` = %s' % str(article_id))

    def get_all(self):
        sdb._ensure_connected()
        return post_list_format(sdb.query("SELECT * FROM `cms_posts` ORDER BY `id` DESC"))

    # 分页
    def get_paged(self, page=1, limit=None, cat=None, title=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `cms_posts` where 1=1"
        if cat:
            sql += " and category = \'%s\'" % cat
        if title:
            sql += " and title like \'%s\'" % title
        sql += " ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    '''获取指定用户发表的所有文章'''

    def get_article_by_author(self, author):
        sql = "SELECT * FROM `cms_posts` where `author` = '%s'" % author
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_max_id(self):
        sdb._ensure_connected()
        maxobj = sdb.query("select max(id) as maxid from `cms_posts`")
        return str(maxobj[0]['maxid'])

    def get_last_post_add_time(self):
        sdb._ensure_connected()
        obj = sdb.get('SELECT `add_time` FROM `cms_posts` ORDER BY `id` DESC LIMIT 1')
        if obj:
            return datetime.fromtimestamp(obj.add_time)
        else:
            return datetime.utcnow() + timedelta(hours=+ 8)

    def get_last_post(self, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        sdb._ensure_connected()
        return post_list_format(
            sdb.query("SELECT * FROM `cms_posts` ORDER BY `id` DESC LIMIT %s" % limit))

    def get_article_detail(self, userid):
        sdb._ensure_connected()
        return post_detail_formate(sdb.get('SELECT * FROM `cms_posts` WHERE `id` = %s LIMIT 1' % str(userid)))

    def get_article_simple(self, userid):
        sdb._ensure_connected()
        return sdb.get(
            'SELECT `id`,`category`,`title`,`comment_num`,`closecomment`,`password` FROM `cms_posts` WHERE `id` = %s' % str(
                userid))

    def get_post_for_sitemap(self, ids=[]):
        sdb._ensure_connected()
        return sdb.query("SELECT `id`,`edit_time` FROM `cms_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
            ','.join(ids), str(len(ids))))


Article = Article()