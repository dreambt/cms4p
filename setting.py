# -*- coding: utf-8 -*-
from os import environ

SAEPY_LOG_VERSION = '0.0.2'
APP_NAME = environ.get("APP_NAME", "")

if 'SERVER_SOFTWARE' in environ:
    debug = False
else:
    debug = True

##下面需要修改
SITE_TITLE = u"数据银行"    # 山东勇胜牌具科技有限公司
SITE_TITLE2 = u"博客标题2"  # 显示在边栏上头（有些模板用不到）
SITE_SUB_TITLE = u"一个简单的运行在SAE上的blog"  #副标题
KEYWORDS = u"变牌衣|变牌包|白光眼镜|单人操作扑克分析仪|挂花药膏|牌九胶花|山东勇胜|勇胜牌具|山东勇胜牌具科技有限公司|山东勇胜牌牌具科技有限公司"
SITE_DECR = u"山东勇胜牌牌具科技有限公司专业销售专业从事销售：变牌衣|变牌包|透视眼镜|单人操作扑克分析仪|挂花药膏|牌九专用胶花|牌九胶花|变牌器|分析仪|牌九胶花"
ADMIN_NAME = u"baitao.ji"
NOTICE_MAIL = u"dreambt@126.com"

###配置邮件发送信息，提醒邮件用的，必须正确填写，建议用Gmail
MAIL_FROM = 'dreambt@gmail.com'
MAIL_SMTP = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_PASSWORD = '{hisense2002j}'
MOVE_SECRET = 'what?'

#放在网页底部的统计代码
ANALYTICS_CODE = """"""
ADSENSE_CODE1 = """"""
ADSENSE_CODE2 = """"""

#使用SAE Storage 服务（保存上传的附件），需在SAE管理面板创建
STORAGE_DOMAIN_NAME = 'attachment'

###设置容易调用的jquery 文件
JQUERY = "http://lib.sinaapp.com/js/jquery/1.6.2/jquery.min.js"

COPY_YEAR = '2011 - 2013'

MAJOR_DOMAIN = '%s.sinaapp.com' % APP_NAME #主域名，默认是SAE 的二级域名
#MAJOR_DOMAIN = 'www.yourdomain.com'

##博客使用的主题，目前可选 default/octopress/octopress-disqus
##你也可以把自己喜欢的wp主题移植过来，
#制作方法参见 http://saepy.sinaapp.com/t/49
THEME = 'sdyspj'

#使用disqus 评论系统，如果你使用就填 website shortname，
#申请地址 http://disqus.com/
DISQUS_WEBSITE_SHORTNAME = ''

####友情链接列表，在管理后台也实现了管理，下面的链接列表仍然有效并排在前面
LINK_BROLL = [
    {"text": '思奇博客', "url": 'http://www.im47.cn'},
]

#当发表新博文时自动ping RPC服务，中文的下面三个差不多了
XML_RPC_ENDPOINTS = [
    'http://blogsearch.google.com/ping/RPC2',
    'http://rpc.pingomatic.com/',
    'http://ping.baidu.com/ping/RPC2'
]

##如果要在本地测试则需要配置Mysql 数据库信息
if debug:
    MYSQL_DB = 'app_cms4p'
    MYSQL_USER = 'root'
    MYSQL_PASS = 'hisense2002j'
    MYSQL_HOST_M = '127.0.0.1'
    MYSQL_HOST_S = '127.0.0.1'
    MYSQL_PORT = '3306'

####除了修改上面的设置，你还需在SAE 后台开通下面几项服务：
# 1 初始化 Mysql
# 2 建立一个名为 attachment 的 Storage
# 3 启用Memcache，初始化大小为1M的 mc，大小可以调，日后文章多了，PV多了可增加
# 4 创建一个 名为 default 的 Task Queue
# 详见 http://saepy.sinaapp.com/t/50 详细安装指南
############## 下面不建议修改 ###########################
if debug:
    BASE_URL = 'http://127.0.0.1:8080'
else:
    BASE_URL = 'http://%s' % MAJOR_DOMAIN

LANGUAGE = 'zh-CN'
COMMENT_DEFAULT_VISIBLE = 1  # 0/1 #发表评论时是否显示 设为0时则需要审核才显示
EACH_PAGE_POST_NUM = 7  # 每页显示文章数
EACH_PAGE_COMMENT_NUM = 10  # 每页评论数
ADMIN_RECENT_COMMENT_NUM = 10 # 在admin界面显示的评论数
RELATIVE_POST_NUM = 5  # 显示相关文章数
SHORTEN_CONTENT_WORDS = 150  # 文章列表截取的字符数
DESCRIPTION_CUT_WORDS = 100  # meta description 显示的字符数
RECENT_COMMENT_NUM = 5  # 边栏显示最近评论数
RECENT_COMMENT_CUT_WORDS = 20  # 边栏评论显示字符数
LINK_NUM = 30  # 边栏显示的友情链接数
MAX_COMMENT_NUM_A_DAY = 30  # 客户端设置Cookie 限制每天发的评论数

PAGE_CACHE = True  # 本地没有 Memcache 服务
PAGE_CACHE_TIME = 3600 * 24  # 默认页面缓存时间
POST_CACHE_TIME = 3600 * 24  # 默认文章缓存时间
COMMON_CACHE_TIME = 3600 * 24  # 通用缓存时间

HOT_TAGS_NUM = 30  # 右侧热门标签显示数
MAX_ARCHIVES_NUM = 50  # 右侧热门标签显示数

MAX_IDLE_TIME = 10  # 数据库最大空闲时间 SAE文档说是30 其实更小，设为5，没问题就不要改了

BLOG_PSW_SUPPORT = True  # 博客支持密码阅读
LINK_BROLL_SUPPORT = False  # sidebar是否支持友情链接
BLOG_BACKUP_SUPPORT = False  # 是否支持博客备份

NUM_SHARDS = 0  # 分片计数器的个数,人少的话用0就可以了，如果由0扩展到比如3，可能程序需要稍微修改一下
if NUM_SHARDS > 0:
    SHARD_COUNT_SUPPORT = True  # 是否支持分片计数器
else:
    SHARD_COUNT_SUPPORT = False

###############################
COOKIE_SECRET = '7nVA0WeZSJSzTCUF8UZB/C3OfLrl7k26iHxfnVa9x0I='
#import base64
#import uuid
#print base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

# REDIS_SERVER = False

# If set to None or 0 the session will be deleted when the user closes the browser.
# If set number the session lives for value days.
PERMANENT_SESSION_LIFETIME = 1  # days

# redis connection config
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0