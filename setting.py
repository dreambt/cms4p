# -*- coding: utf-8 -*-
from os import environ

APP_VERSION = '0.0.1'
APP_NAME = environ.get("APP_NAME", "taofeng139")

if 'sae.kvdb.file' in environ:
    debug = True
else:
    debug = False

################
# 网站常量配置 1 #
################
SITE_TITLE = u"涛锋培训"
SITE_TITLE2 = u"绿色便捷的打印新时代"
SITE_SUB_TITLE = u"CloudPrint.Me"  # 副标题
KEYWORDS = u"CloudPrint,云,打印,山东财经大学,创业,绿色,环保,省时"
SITE_DECR = u"CloudPrint 是一个 ********"


################
# 网站常量配置 2 #
################
COPY_YEAR = '2013'
LANGUAGE = 'zh-CN'
ADMIN_NAME = u"baitao.ji"
NOTICE_MAIL = u"dreambt@126.com"
MOVE_SECRET = 'what?'  # 迁移密码
THEME = 'taofeng139'


##############
# 邮件服务设置 #
##############
MAIL_FROM = 'postmaster@sdyspj.sendcloud.org'
MAIL_KEY = 'DSvK6ViH'
MAIL_SMTP = 'smtpcloud.sohu.com'
MAIL_PORT = 25
# 收集报错信息用的邮箱
MAIL_TO = 'dev@cms4p.sendcloud.org'


###########
# 统计代码 #
###########
ANALYTICS_CODE = """"""
ADSENSE_CODE1 = """"""
ADSENSE_CODE2 = """"""


##############
# 后台界面设置 #
##############
# 文章相关
EACH_PAGE_POST_NUM = 7  # 每页显示文章数
SHORTEN_CONTENT_WORDS = 512  # 文章列表截取的字符数
DESCRIPTION_CUT_WORDS = 100  # meta description 显示的字符数
RELATIVE_POST_NUM = 5  # 显示相关文章数

# 评论相关
EACH_PAGE_COMMENT_NUM = 10  # 每页评论数
RECENT_COMMENT_NUM = 5  # 边栏显示最近评论数
RECENT_COMMENT_CUT_WORDS = 20  # 边栏评论显示字符数
MAX_COMMENT_NUM_A_DAY = 30  # 客户端设置Cookie 限制每天发的评论数
COMMENT_DEFAULT_VISIBLE = 1  # 0/1 #发表评论时是否显示 设为0时则需要审核才显示

# 缓存相关
PAGE_CACHE_TIME = 3600 * 24  # 默认页面缓存时间

# 其他相关
LINK_NUM = 30  # 边栏显示的友情链接数
HOT_TAGS_NUM = 30  # 右侧热门标签显示数
MAX_ARCHIVES_NUM = 50  # 右侧热门标签显示数

# 后台界面设置
ADMIN_CATEGORY_NUM = 12
ADMIN_POST_NUM = 12
ADMIN_COMMENT_NUM = 12
ADMIN_USER_NUM = 12
ADMIN_LINK_NUM = 12

NUM_SHARDS = 0  # 分片计数器的个数,人少的话用0就可以了，如果由0扩展到比如3，可能程序需要稍微修改一下
if NUM_SHARDS > 0:
    SHARD_COUNT_SUPPORT = True  # 是否支持分片计数器
else:
    SHARD_COUNT_SUPPORT = False

LINK_BROLL = [
    {"text": '思奇博客', "url": 'http://www.im47.cn'},
]

# 当发表新博文时自动ping RPC服务，中文的下面三个差不多了
XML_RPC_ENDPOINTS = [
    'http://blogsearch.google.com/ping/RPC2',
    'http://rpc.pingomatic.com/',
    'http://ping.baidu.com/ping/RPC2'
]

# 安全密钥
COOKIE_SECRET = '7nVA0WeZSJSzTCUF8UZB/C3OfLrl7k26iHxfnVa9x0I='
#import base64
#import uuid
#print base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


#######################
# 静态资源文件 CDN 加速 #
######################
if debug:
    MAJOR_DOMAIN = '%s.sinaapp.com' % APP_NAME
    BASE_URL = 'http://localhost:8081'
    STATIC_URL = BASE_URL
    JQUERY = "http://lib.sinaapp.com/js/jquery/2.0.2/jquery-2.0.2.min.js"
    JQUERY_IE = "http://lib.sinaapp.com/js/jquery/1.10.1/jquery-1.10.1.min.js"
else:
    BASE_URL = 'http://1.cloudprint.sinaapp.com'
    STATIC_URL = BASE_URL
    JQUERY = STATIC_URL + "/static/js/vender/jquery-2.0.2.min.js"
    JQUERY_IE = STATIC_URL + "/static/js/vender/jquery-1.10.1.min.js"


############
# KV 数据库 #
############
if not debug:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379


#########
# 云存储 #
#########
#使用SAE Storage 服务（保存上传的附件），需在SAE管理面板创建
DEFAULT_BUCKET = 'attachment'


###############
# MySQL 数据库 #
###############
if debug:
    MYSQL_DB = 'app_cms4p'
    MYSQL_USER = 'root'
    MYSQL_PASS = 'hisense2002j'
    MYSQL_HOST_M = '127.0.0.1'
    MYSQL_HOST_S = '127.0.0.1'
    MYSQL_PORT = '3306'
    MAX_IDLE_TIME = 10
else:
    MYSQL_DB = 'app_taofeng139'
    MYSQL_USER = 'root'
    MYSQL_PASS = 'hisense2012JBT'
    MYSQL_HOST_M = 'localhost'
    MYSQL_HOST_S = 'localhost'
    MYSQL_PORT = '3306'
    MAX_IDLE_TIME = 30


# BASE_URL = 'http://%s' % MAJOR_DOMAIN
# STATIC_URL = 'http://cms4p.sinaapp.com'
# import sae.const
#
# MYSQL_DB = sae.const.MYSQL_DB
# MYSQL_USER = sae.const.MYSQL_USER
# MYSQL_PASS = sae.const.MYSQL_PASS
# MYSQL_HOST_M = sae.const.MYSQL_HOST
# MYSQL_HOST_S = sae.const.MYSQL_HOST_S
# MYSQL_PORT = sae.const.MYSQL_PORT
