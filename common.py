# -*- coding: utf-8 -*-
import re
import os.path
from urllib import unquote, quote
from datetime import datetime, timedelta
import requests

import tornado.web

import tenjin
from tenjin.helpers import *
from setting import *

from extensions.sessions import Session, RedisSession

#KVDB 要在后台初始化
import sae.kvdb

kv = sae.kvdb.KVClient()

#Memcache 是否可用、用户是否在后台初始化Memcache
MC_Available = False
if PAGE_CACHE:
    import pylibmc

    mc = pylibmc.Client() #只需初始化一次？
    try:
        MC_Available = mc.set('mc_available', '1', 3600)
    except:
        pass


def slugfy(text, separator='-'):
    text = text.lower()
    text = re.sub("[¿_\-　，。：；‘“’”【】『』§！－——＋◎＃￥％……※×（）《》？、÷]+", ' ', text)
    ret_list = []
    for c in text:
        ordnum = ord(c)
        if 47 < ordnum < 58 or 96 < ordnum < 123:
            ret_list.append(c)
        else:
            if re.search(u"[\u4e00-\u9fa5]", c):
                ret_list.append(c)
            else:
                ret_list.append(' ')
    ret = ''.join(ret_list)
    ret = re.sub(r"\ba\b|\ban\b|\bthe\b", '', ret)
    ret = ret.strip()
    ret = re.sub("[\s]+", separator, ret)
    return ret


def safe_encode(con):
    return con.replace("<", "&lt;").replace(">", "&gt;")


def safe_decode(con):
    return con.replace("&lt;", "<").replace("&gt;", ">")


def unquoted_unicode(string, coding='utf-8'):
    return unquote(string).decode(coding)


def quoted_string(unicode, coding='utf-8'):
    return quote(unicode.encode(coding))


def cnnow():
    return datetime.utcnow() + timedelta(hours=+ 8)


def genArchive():
    #return "201207"
    return cnnow().strftime("%Y%m")


# get time_from_now
def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp)


def time_from_now(time):
    # return datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(time, int):
        time = timestamp_to_datetime(time)
        #time_diff = datetime.utcnow() - time
    time_diff = cnnow() - time
    days = time_diff.days
    if days:
        if days > 730:
            return '%s 年前' % (days / 365)
        if days > 365:
            return '1 年前'
        if days > 60:
            return '%s 个月前' % (days / 30)
        if days > 30:
            return '1 个月前'
        if days > 14:
            return '%s 周前' % (days / 7)
        if days > 7:
            return '1 周前'
        if days > 1:
            return '%s 天前' % days
        return '1 天前'
    seconds = time_diff.seconds
    if seconds > 7200:
        return '%s 小时前' % (seconds / 3600)
    if seconds > 3600:
        return '1 小时前'
    if seconds > 120:
        return '%s 分钟前' % (seconds / 60)
    if seconds > 60:
        return '1 分钟前'
    if seconds > 1:
        return '%s 秒前' % seconds
    return '%s 秒前' % seconds


def clear_cache_by_pathlist(pathlist=[]):
    if pathlist and MC_Available:
        try:
            mc = pylibmc.Client()
            mc.delete_multi([str(p) for p in pathlist])
        except:
            pass


def clear_all_cache():
    if PAGE_CACHE:
        try:
            mc = pylibmc.Client()
            mc.flush_all()
        except:
            pass
    else:
        pass


def format_date(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


def memcached(key, cache_time=0, key_suffix_calc_func=None):
    def wrap(func):
        def cached_func(*args, **kw):
            if not MC_Available:
                return func(*args, **kw)

            key_with_suffix = key
            if key_suffix_calc_func:
                key_suffix = key_suffix_calc_func(*args, **kw)
                if key_suffix is not None:
                    key_with_suffix = '%s:%s' % (key, key_suffix)

            mc = pylibmc.Client()
            value = mc.get(key_with_suffix)
            if value is None:
                value = func(*args, **kw)
                try:
                    mc.set(key_with_suffix, value, cache_time)
                except:
                    pass
            return value

        return cached_func

    return wrap


RQT_RE = re.compile('<span id="requesttime">\d*</span>', re.I)
PV_RE = re.compile('<span class="categories greyhref">PageView.*?</span>', re.I)


def pagecache(key="", time=PAGE_CACHE_TIME, key_suffix_calc_func=None):
    def _decorate(method):
        def _wrapper(*args, **kwargs):
            if not MC_Available:
                method(*args, **kwargs)
                return

            req = args[0]

            key_with_suffix = key
            if key_suffix_calc_func:
                key_suffix = key_suffix_calc_func(*args, **kwargs)
                if key_suffix:
                    key_with_suffix = '%s:%s' % (key, quoted_string(key_suffix))

            if key_with_suffix:
                key_with_suffix = str(key_with_suffix)
            else:
                key_with_suffix = req.request.path

            mc = pylibmc.Client()
            html = mc.get(key_with_suffix)
            # request_time = int(req.request.request_time() * 1000)
            if html:
                if key == 'post':
                    if key_suffix:
                        keyname = 'pv_%s' % (quoted_string(key_suffix))
                        pvcookie = req.get_cookie(keyname, '0')
                        # print keyname,pvcookie
                        if int(pvcookie) == 0:
                            req.set_cookie(keyname, '1', path="/", expires_days=1)  # 不同浏览器有不同cookie
                            increment(keyname)
                        count = get_count(keyname)
                        print count
                        req.write(PV_RE.sub('<span class="categories greyhref">PageView(%d)</span>' % count, html))
                        return _wrapper
                req.write(html)
                #req.write(RQT_RE.sub('<span id="requesttime">%d</span>'%request_time, html))
            else:
                result = method(*args, **kwargs)
                print time
                mc.set(key_with_suffix, result, time)

        return _wrapper

    return _decorate

###
engine = tenjin.Engine(path=[os.path.join('templates', theme) for theme in [THEME, 'admin']] + ['templates'],
                       cache=tenjin.MemoryCacheStorage(), preprocess=True)


class BaseHandler(tornado.web.RequestHandler):
    def render(self, template, context=None, globals=None, layout=False):
        if context is None:
            context = {}
        context.update({
            'request': self.request,
        })
        return engine.render(template, context, globals, layout)

    def echo(self, template, context=None, globals=None, layout=False):
        self.write(self.render(template, context, globals, layout))

    def set_cache(self, seconds, is_privacy=None):
        if seconds <= 0:
            self.set_header('Cache-Control', 'no-cache')
            #self.set_header('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT')
        else:
            if is_privacy:
                privacy = 'public, '
            elif is_privacy is None:
                privacy = ''
            else:
                privacy = 'private, '
            self.set_header('Cache-Control', '%smax-age=%s' % (privacy, seconds))

    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session
        else:
            self.require_setting('permanent_session_lifetime', 'session')
            expires = self.settings['permanent_session_lifetime'] or None
            if 'redis_server' in self.settings and self.settings['redis_server']:
                sessionid = self.get_secure_cookie('sid')
                self._session = RedisSession(self.application.session_store, sessionid, expires_days=expires)
                if not sessionid:
                    self.set_secure_cookie('sid', self._session.id, expires_days=expires)
            else:
                self._session = Session(self.get_secure_cookie, self.set_secure_cookie, expires_days=expires)
            return self._session

    def isAuthor(self):
        user_name_cookie = self.get_secure_cookie('username', '')
        user_pw_cookie = self.get_secure_cookie('userpw', '')
        if user_name_cookie and user_pw_cookie:
            from model import User

            user = User.check_user(user_name_cookie, user_pw_cookie)
        else:
            user = False
        return user

    # http://www.keakon.net/2012/12/03/Tornado%E4%BD%BF%E7%94%A8%E7%BB%8F%E9%AA%8C
    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            sendEmail("404 页面找不到", "")
            self.render('404.html')
        elif status_code == 500:
            sendEmail("500 页面找不到", "")
            self.render('500.html')
        else:
            sendEmail("*** 未知异常", "")
            super(tornado.web.RequestHandler, self).write_error(status_code, **kwargs)


def authorized(url='/admin/login'):
    def wrap(handler):
        def authorized_handler(self, *args, **kw):
            request = self.request
            user_name_cookie = self.get_secure_cookie('username')
            user_pw_cookie = self.get_secure_cookie('userpw')
            if user_name_cookie and user_pw_cookie:
                from model import User

                user = User.check_user(user_name_cookie, user_pw_cookie)
            else:
                user = False
            if request.method == 'GET':
                if not user:
                    self.redirect(url)
                    return False
                else:
                    handler(self, *args, **kw)
            else:
                if not user:
                    self.error(403)
                else:
                    handler(self, *args, **kw)

        return authorized_handler

    return wrap


def client_cache(seconds, privacy=None):
    def wrap(handler):
        def cache_handler(self, *args, **kw):
            self.set_cache(seconds, privacy)
            return handler(self, *args, **kw)

        return cache_handler

    return wrap


# 以下是在SAE上的计数器实现
import random


def get_count(keyname, num_shards=NUM_SHARDS, value=1):
    """Retrieve the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    if num_shards:
        total = 0
        for index in range(0, num_shards):
            shard_name = "%s:%s" % (str(keyname), str(index))
            count = kv.get(shard_name)
            if count:
                total += count
    else:
        total = kv.get(keyname)
        if total is None:
            total = value
            kv.set(keyname, total)
    return total


def set_count(keyname, num_shards=NUM_SHARDS, value=1):
    """Retrieve the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    if num_shards:
        #TODO
        total = 0
        for index in range(0, num_shards):
            shard_name = "%s:%s" % (str(keyname), str(index))
            count = kv.get(shard_name)
            if count:
                total += count
    else:
        kv.set(keyname, value)


def increment(keyname, num_shards=NUM_SHARDS, value=1):
    """Increment the value for a given sharded counter.

    Parameters:
      name - The name of the counter
    """
    if num_shards:
        index = random.randint(0, num_shards - 1)
        shard_name = "%s:%s" % (str(keyname), str(index))
        count = kv.get(shard_name)
        if count is None:
            count = 0
        count += value
        kv.set(shard_name, count)
    else:
        count = kv.get(keyname)
        if count is None:
            count = 0
        count += value
        kv.set(keyname, count)
    return count

# 发送邮件
def sendEmail(subject, html, to=None):
    url = "https://sendcloud.sohu.com/webapi/mail.send.xml"
    if to:
        to = getAttr('MAIL_TO')
    params = {
        "api_user": getAttr('MAIL_FROM'),
        "api_key": getAttr('MAIL_KEY'),
        "to": to,
        "from": getAttr('MAIL_FROM'),
        "formname": getAttr('SITE_TITLE'),
        "subject": subject,
        "html": html
    }
    r = requests.post(url, params)
    print r.text


# 清空 KVDB 缓存
def clearAllKVDB():
    total = get_count('Totalblog', NUM_SHARDS, 0)
    for loop in range(0, total + 1):
        keyname = 'pv_%d' % (loop)
        kv.delete(keyname)
    kv.delete('Totalblog')


# 设置属性
def getAttr(keyname):
    value = mc.get(keyname)
    if value is None:
        value = kv.get(keyname)
        if value:
            mc.set(keyname, value, COMMON_CACHE_TIME)
    return value


def setAttr(keyname, value):
    mc.set(keyname, value, COMMON_CACHE_TIME)
    kv.set(keyname, value)