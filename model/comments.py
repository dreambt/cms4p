# -*- coding: utf-8 -*-
from hashlib import md5
from core.common import getAttr, time_from_now
from model import sdb, mdb, HTML_REG
from setting import EACH_PAGE_COMMENT_NUM, RECENT_COMMENT_CUT_WORDS

_author__ = 'baitao.ji'


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


class Comments():
    def count_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT COUNT(*) AS num FROM `cms_comments`')[0]['num']

    def create(self, params):
        query = "INSERT INTO `cms_comments` (`post_id`, `user_name`, `email`, `website`, `content`, `status`) " \
                "values(%s,%s,%s,%s,%s,%s)"
        mdb._ensure_connected()
        return mdb.execute(query, params['post_id'], params['user_name'], params['email'], params['website'],
                           params['content'], params['status'])

    def update(self, params):
        query = "UPDATE `cms_comments` SET `content` = %s WHERE `comment_id` = %s LIMIT 1"
        mdb._ensure_connected()
        mdb.execute(query, params['content'], params['comment_id'])
        return params['comment_id']

    def delete(self, comment_id):
        cobj = self.get(comment_id)
        post_id = cobj.post_id
        from model.articles import Articles

        pobj = Articles.get(post_id)

        mdb._ensure_connected()
        mdb.execute("DELETE FROM `cms_comments` WHERE `comment_id` = %s LIMIT 1", comment_id)
        if pobj:
            Articles.update_comment_num(pobj.comment_num - 1, post_id)
        return

    def get(self, comment_id):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_comments` WHERE `comment_id` = %s' % str(comment_id))

    # 分页
    def get_paged(self, page=1, limit=None):
        if limit is None:
            limit = getAttr('ADMIN_COMMENT_NUM')
        limit = int(limit)
        sdb._ensure_connected()
        sql = "SELECT * FROM `cms_comments` ORDER BY `id` DESC LIMIT %s,%s" % ((int(page) - 1) * limit, limit)
        return comment_format_admin(sdb.query(sql))

    def get_recent_comments(self, limit=None):
        if limit is None:
            limit = getAttr('RECENT_COMMENT_NUM')
        sdb._ensure_connected()
        return comment_format(sdb.query('SELECT * FROM `cms_comments` ORDER BY `comment_id` DESC LIMIT %s' % limit))

    def get_post_page_comments_by_id(self, post_id=0, min_comment_id=0, limit=EACH_PAGE_COMMENT_NUM):
        if min_comment_id == 0:
            sdb._ensure_connected()
            return comment_format(sdb.query(
                'SELECT * FROM `cms_comments` WHERE `postid`= %s ORDER BY `comment_id` DESC LIMIT %s' % (
                    str(post_id), str(limit))))
        else:
            sql = "SELECT * FROM `cms_comments` WHERE `postid`= %s AND `comment_id` < %s " \
                  "ORDER BY `comment_id` DESC LIMIT %s"
            sdb._ensure_connected()
            return comment_format(sdb.query(
                sql % (
                    str(post_id), str(min_comment_id), str(limit))))

Comments = Comments()