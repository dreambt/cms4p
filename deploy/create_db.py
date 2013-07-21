#!/usr/bin/env python
# -*- coding: utf-8 -*-
from model import mdb

_author__ = 'baitao.ji'

"""
用于创建数据库，请按照下面的要求填写相关的信息，再运行`python create_db.py`，
https://github.com/SerhoLiu/serholiu.com/blob/master/tools/create_db.py
"""


def create_db():
    sql = """
DROP TABLE IF EXISTS `cms_user`;
CREATE TABLE IF NOT EXISTS `cms_user` (
  `user_id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_name` varchar(40) NOT NULL DEFAULT '',
  `email` varchar(40) NOT NULL DEFAULT '',
  `password` varchar(32) NOT NULL DEFAULT '',
  `salt` varchar(8) NOT NULL DEFAULT '',
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`user_id`),
  KEY `user_name` (`user_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `cms_role`;
CREATE TABLE IF NOT EXISTS `cms_role` (
  `role_id` int unsigned NOT NULL AUTO_INCREMENT,
  `role_name` varchar(20) NOT NULL DEFAULT '',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`role_id`),
  KEY `role_name` (`role_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `cms_user_role`;
CREATE TABLE IF NOT EXISTS `cms_user_role` (
  `user_id` int unsigned NOT NULL,
  `role_id` int unsigned NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `cms_function`;
CREATE TABLE IF NOT EXISTS `cms_function` (
  `function_id` int unsigned NOT NULL AUTO_INCREMENT,
  `function_name` varchar(20) NOT NULL DEFAULT '',
  `url` varchar(80) NOT NULL DEFAULT '',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`function_id`),
  KEY `function_name` (`function_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `cms_role_function`;
CREATE TABLE IF NOT EXISTS `cms_role_function` (
  `role_id` int unsigned NOT NULL,
  `function_id` int unsigned NOT NULL,
  PRIMARY KEY (`role_id`, `function_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `cms_category`;
CREATE TABLE IF NOT EXISTS `cms_category` (
  `category_id` int unsigned NOT NULL AUTO_INCREMENT,
  `father_category_id` int unsigned NOT NULL DEFAULT '0',
  `category_name` varchar(20) NOT NULL DEFAULT '',
  `display_order` tinyint(3) NOT NULL DEFAULT 0,
  `show_type` varchar(10) NOT NULL DEFAULT 'default',
  `description` varchar(500) NOT NULL,
  `allow_comment` TINYINT(1) NOT NULL DEFAULT 1,
  `allow_publish` TINYINT(1) NOT NULL DEFAULT 1,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`category_id`),
  KEY `category_name` (`category_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_show_type`;
CREATE TABLE IF NOT EXISTS `cms_show_type` (
  `type_key` varchar(20) NOT NULL DEFAULT '',
  `type_name` varchar(20) NOT NULL DEFAULT '',
  KEY `type_key` (`type_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_posts`;
CREATE TABLE IF NOT EXISTS `cms_posts` (
  `post_id` int unsigned NOT NULL AUTO_INCREMENT,
  `category_id` int unsigned NOT NULL DEFAULT 0,
  `user_id` int unsigned NOT NULL DEFAULT 0,
  `title` varchar(100) NOT NULL DEFAULT '',
  `tags` VARCHAR(255) NOT NULL DEFAULT '',
  `digest` VARCHAR(500) NOT NULL DEFAULT '',
  `content` mediumtext NOT NULL,
  `image_url` varchar(80) NOT NULL DEFAULT '',
  `password` varchar(32) NOT NULL DEFAULT '',
  `salt` varchar(8) NOT NULL DEFAULT '',
  `top` TINYINT(1) NOT NULL DEFAULT 0,
  `rate` TINYINT(3) NOT NULL DEFAULT 0,
  `rate_times` int unsigned NOT NULL DEFAULT 0,
  `views` int unsigned NOT NULL DEFAULT 0,
  `comment_num` int unsigned NOT NULL DEFAULT 0,
  `allow_comment` TINYINT(1) NOT NULL DEFAULT 1,
  `status` TINYINT(1) NOT NULL DEFAULT 1,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`post_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_archive`;
CREATE TABLE IF NOT EXISTS `cms_archive` (
  `archive_id` int unsigned NOT NULL AUTO_INCREMENT,
  `archive_name` varchar(17) NOT NULL DEFAULT '',
  `post_num` int unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`archive_id`),
  KEY `archive_name` (`archive_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_archive_post`;
CREATE TABLE IF NOT EXISTS `cms_archive_post` (
  `archive_id` int unsigned NOT NULL,
  `post_id` int unsigned NOT NULL,
  PRIMARY KEY (`archive_id`, `post_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_comments`;
CREATE TABLE IF NOT EXISTS `cms_comments` (
  `comment_id` int unsigned NOT NULL AUTO_INCREMENT,
  `post_id` int unsigned NOT NULL DEFAULT 0,
  `user_name` varchar(40) NOT NULL DEFAULT '',
  `email` varchar(40) NOT NULL DEFAULT '',
  `website` varchar(80) NOT NULL DEFAULT '',
  `content` mediumtext NOT NULL,
  `status` TINYINT(1) NOT NULL DEFAULT 1,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`comment_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_links`;
CREATE TABLE IF NOT EXISTS `cms_links` (
  `link_id` int unsigned NOT NULL AUTO_INCREMENT,
  `link_name` varchar(100) NOT NULL DEFAULT '',
  `url` varchar(200) NOT NULL DEFAULT '',
  `display_order` tinyint(3) NOT NULL DEFAULT 0,
  `status` TINYINT(1) NOT NULL DEFAULT 1,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `last_modified_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` TIMESTAMP NOT NULL DEFAULT '2013-07-21 17:00:41',
  PRIMARY KEY (`link_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `cms_tags`;
CREATE TABLE IF NOT EXISTS `cms_tags` (
  `tag_id` int unsigned NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(20) NOT NULL DEFAULT '',
  `tag_hot` int unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`tag_id`),
  KEY `tag_name` (`tag_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;


INSERT INTO cms_category (category_id, father_category_id, category_name, display_order, show_type, url, description, allow_comment, allow_publish, deleted, last_modified_date, created_date) VALUES (0, 0, '顶级菜单', 0, 'url', '', '', false, true, false, '2013-07-21 16:20:56', '2013-07-21 16:13:12');

insert into cms_show_types values ('default', '默认显示');
insert into cms_show_types values ('list', '简单列表');
insert into cms_show_types values ('digest', '摘要列表');
insert into cms_show_types values ('pic', '图片瀑布');
insert into cms_show_types values ('video', '视频瀑布');
insert into cms_show_types values ('url', 'URL 网址');
"""
    mdb._ensure_connected()
    mdb.execute(sql)


def flush_all_data(self):
    sql = """
        TRUNCATE TABLE `cms_category`;
        TRUNCATE TABLE `cms_comments`;
        TRUNCATE TABLE `cms_links`;
        TRUNCATE TABLE `cms_posts`;
        TRUNCATE TABLE `cms_tags`;
        TRUNCATE TABLE `cms_archive`;
        TRUNCATE TABLE `cms_user`;
        TRUNCATE TABLE `cms_role`;
        TRUNCATE TABLE `cms_user_role`;
        """
    mdb._ensure_connected()
    mdb.execute(sql)


if __name__ == '__main__':
    print "开始创建数据库..."
    create_db()
    print "数据库创建完毕！"