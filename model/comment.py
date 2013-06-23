# -*- coding: utf-8 -*-
from hashlib import md5
from core.common import getAttr, time_from_now
from model.base import sdb, mdb, HTML_REG
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
        from model.article import Article
        pobj = Article.get_article(postid)

        mdb._ensure_connected()
        mdb.execute("DELETE FROM `sp_comments` WHERE `id` = %s LIMIT 1", id)
        if pobj:
            from model.article import Article
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