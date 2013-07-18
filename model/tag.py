# -*- coding: utf-8 -*-
from model.article import post_list_format
from model.base import mdb, sdb
from setting import EACH_PAGE_POST_NUM, HOT_TAGS_NUM

_author__ = 'baitao.ji'


class Tag():
    def get_all_tag_name(self):
        #for add/edit post
        sdb._ensure_connected()
        return sdb.query('SELECT `name` FROM `cms_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_hot_tag_name(self):
        #for sider
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `cms_tags` ORDER BY `id_num` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_tag_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_tags` WHERE `name` = \'%s\'' % name)

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
                "SELECT * FROM `cms_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), len(getids))))
        else:
            return []

    def add_postid_to_tags(self, tags=[], postid=''):
        mdb._ensure_connected()
        for tag in tags:
            obj = mdb.get('SELECT * FROM `cms_tags` WHERE `name` = \'%s\'' % tag)

            if obj:
                query = "UPDATE `cms_tags` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
                mdb.execute(query, "%s," % postid, obj.id)
            else:
                query = "INSERT INTO `cms_tags` (`name`,`id_num`,`content`) values(%s,1,%s)"
                mdb.execute(query, tag, postid)

    def remove_postid_from_tags(self, tags=[], postid=''):
        mdb._ensure_connected()
        for tag in tags:
            obj = mdb.get('SELECT * FROM `cms_tags` WHERE `name` = \'%s\'' % tag)

            if obj:
                idlist = obj.content.split(',')
                if postid in idlist:
                    idlist.remove(postid)
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist) == 0:
                        mdb.execute("DELETE FROM `cms_tags` WHERE `id` = %s LIMIT 1", obj.id)
                    else:
                        query = "UPDATE `cms_tags` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                        mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
                else:
                    pass


Tag = Tag()