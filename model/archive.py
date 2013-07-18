# -*- coding: utf-8 -*-
from model.article import post_list_format
from model.base import mdb, sdb
from setting import EACH_PAGE_POST_NUM

_author__ = 'baitao.ji'


class Archive():
    def get_latest_archive_name(self):
        sdb._ensure_connected()
        objs = sdb.get('SELECT `name` FROM `cms_archive` ORDER BY `name` DESC')
        print objs[0].name
        return objs[0].name

    def get_all_archive_name(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `name`,`id_num` FROM `cms_archive` ORDER BY `name` DESC')

    def get_all(self):
        sdb._ensure_connected()
        return sdb.query('SELECT * FROM `cms_archive` ORDER BY `name` DESC')

    def get_all_archive_id(self):
        sdb._ensure_connected()
        return sdb.query('SELECT `id` FROM `cms_archive` ORDER BY `id` DESC')

    def get_archive_by_name(self, name=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_archive` WHERE `name` = \'%s\'' % name)

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
                "SELECT * FROM `cms_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (
                    ','.join(getids), str(len(getids)))))
        else:
            return []

    def add_postid_to_archive(self, name='', postid=''):
        mdb._ensure_connected()
        #因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
        obj = mdb.get('SELECT * FROM `cms_archive` WHERE `name` = \'%s\'' % name)

        if obj:
            query = "UPDATE `cms_archive` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
            mdb.execute(query, "%s," % postid, obj.id)
        else:
            query = "INSERT INTO `cms_archive` (`name`,`id_num`,`content`) values(%s,1,%s)"
            mdb.execute(query, name, postid)

    def remove_postid_from_archive(self, name='', postid=''):
        mdb._ensure_connected()
        obj = mdb.get('SELECT * FROM `cms_archive` WHERE `name` = \'%s\'' % name)
        if obj:
            idlist = obj.content.split(',')
            if postid in idlist:
                idlist.remove(postid)
                try:
                    idlist.remove('')
                except:
                    pass
                if len(idlist) == 0:
                    mdb.execute("DELETE FROM `cms_archive` WHERE `id` = %s LIMIT 1", obj.id)
                else:
                    query = "UPDATE `cms_archive` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                    mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
            else:
                pass

    def get_archive(self, id=''):
        sdb._ensure_connected()
        return sdb.get('SELECT * FROM `cms_archive` WHERE `id` = %s' % str(id))


Archive = Archive()