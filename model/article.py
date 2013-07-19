# -*- coding: utf-8 -*-
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
    def count_all(self, category_id=None, title=None):
        sdb._ensure_connected()
        sql = "SELECT COUNT(*) AS num FROM `cms_posts` WHERE 1=1"
        if category_id:
            sql += " and category_id = \'%s\'" % category_id
        if title:
            sql += " and title like \'%s\'" % title
        return sdb.query(sql)[0]['num']

    def create(self, params):
        query = "INSERT INTO `cms_posts` (`category_id`, `user_id`，`title`, `tags`, `digest`, `content`, " \
                "`image_url`, `password`, `salt`, `top`, `allow_comment`) " \
                "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['category_id'], params['user_id'], params['title'], params['tags'],
                           params['digest'], params['content'], params['image_url'], params['password'],
                           params['salt'], params['top'], params['allow_comment'])

    def update(self, params):
        sql = "UPDATE `cms_posts` SET "
        sql += "`category_id` = %s," % params['category_id']
        sql += "`title` = %s," % params['title']
        sql += "`tags` = %s," % params['tags']
        sql += "`digest` = %s," % params['digest']
        sql += "`content` = %s," % params['content']
        sql += "`image_url` = %s," % params['image_url']
        sql += "`password` = %s," % params['password']
        sql += "`salt` = %s," % params['salt']
        sql += "`image_url` = %s," % params['image_url']
        sql += "`top` = %s," % params['top']
        sql += "`allow_comment` = %s," % params['allow_comment']
        sql += "`post_id` = %s where `post_id` = %s"
        mdb._ensure_connected()
        mdb.execute(sql, params['post_id'], params['post_id'])
        return params['post_id']

    def update_post_edit_author(self, post_id, user_id):
        sql = "UPDATE `cms_posts` SET `user_id` = %s WHERE `post_id` = %s LIMIT 1" % (user_id, post_id)
        mdb._ensure_connected()
        mdb.execute(sql)

    def update_comment_num(self, num=1, post_id=''):
        query = "UPDATE `cms_posts` SET `comment_num` = %s WHERE `post_id` = %s LIMIT 1"
        mdb._ensure_connected()
        return mdb.execute(query, num, post_id)

    def delete(self, post_id=''):
        if post_id:
            mdb._ensure_connected()
            mdb.execute("DELETE FROM `cms_posts` WHERE `post_id` = %s LIMIT 1", post_id)
            mdb.execute("DELETE FROM `cms_comments` WHERE `post_id` = %s", post_id)

    def get(self, post_id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_posts` WHERE `post_id` = %s' % str(post_id))

    def get_all(self):
        sdb._ensure_connected()
        return post_list_format(sdb.query("SELECT * FROM `cms_posts` ORDER BY `post_id` DESC"))

    # 分页
    def get_paged(self, page=1, limit=None, category_id=None, title=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        limit = int(limit)
        sql = "SELECT * FROM `cms_posts` where 1=1"
        if category_id:
            sql += " and category_id = \'%s\'" % category_id
        if title:
            sql += " and title like \'%s\'" % title
        sql += " ORDER BY `post_id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        sdb._ensure_connected()
        return sdb.query(sql)

    '''获取指定用户发表的所有文章'''

    def get_post_by_author(self, user_id):
        sql = "SELECT * FROM `cms_posts` where `user_id` = '%s'" % user_id
        sdb._ensure_connected()
        return sdb.query(sql)

    def get_last_post(self, limit=None):
        if limit is None:
            limit = getAttr('EACH_PAGE_POST_NUM')
        sdb._ensure_connected()
        return post_list_format(
            sdb.query("SELECT * FROM `cms_posts` ORDER BY `post_id` DESC LIMIT %s" % limit))

    def get_post_detail(self, post_id):
        sql = 'SELECT p.*,`user_name`,`category_name` FROM `cms_posts` p ' \
              'inner join `cms_category` c on p.category_id=c.category_id and p.`post_id` = %s ' \
              'inner join `cms_user` u on p.user_id=u.user_id'
        sdb._ensure_connected()
        return post_detail_formate(sdb.get(sql, str(post_id)))

    def get_post_simple(self, post_id):
        sql = 'SELECT `post_id`,`user_name`,`category_name`,`title`,`comment_num`,`closecomment`,`password` FROM `cms_posts` p ' \
              'inner join `cms_category` c on p.category_id=c.category_id and p.`post_id` = %s ' \
              'inner join `cms_user` u on p.user_id=u.user_id'
        sdb._ensure_connected()
        return sdb.get(sql, post_id)

    def get_post_for_sitemap(self, ids=[]):
        sdb._ensure_connected()
        return sdb.query("SELECT `post_id`,`last_modified_date` FROM `cms_posts` "
                         "WHERE `post_id` in(%s) ORDER BY `post_id` DESC LIMIT %s" % (','.join(ids), str(len(ids))))


Article = Article()