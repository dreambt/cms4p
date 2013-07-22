# -*- coding: utf-8 -*-
import StringIO
from hashlib import md5
import re
import time

from core.common import BaseHandler, authorized, clear_cache_by_pathlist, clear_all_cache, setAttr, clearAllKVDB, getAttr, sendEmail
from core.storage import put_storage, get_storage_list
from core.utils.random_utils import random_int
from model.posts import Posts
from model.users import Users
from setting import *
from extensions.imagelib import Recaptcha, Thumbnail

try:
    import json
except:
    import simplejson as json

if not debug:
    from sae.taskqueue import add_task


class HomePage(BaseHandler):
    @authorized()
    def get(self):
        output = self.render('admin_index.html', {
            'title': "后台首页",
            'keywords': getAttr('KEYWORDS'),
            'description': getAttr('SITE_DECR'),
            'test': '',
        }, layout='_layout_admin.html')
        self.write(output)
        return output


class Login(BaseHandler):
    def get(self):
        self.echo('admin_login.html')

    def post(self):
        self.set_header("Content-Type", "application/json")

        try:
            name_or_email = self.get_argument("name_or_email").encode('utf-8')
            password = self.get_argument("password").encode('utf-8')
            captcha = self.get_argument("captcha").encode('utf-8')
        except:
            self.write(json.dumps("用户名、密码、验证码均为必填项！"))
            return

        if self.get_secure_cookie("captcha") != captcha:
            self.write(json.dumps("验证码填写错误或用户不存在！"))
            return

        has_user = Users.get_by_name_or_email(name_or_email)
        if has_user and has_user.status == 1 and has_user.deleted == 0:
            password += has_user.salt
            password = md5(password.encode('utf-8')).hexdigest()
            if password == has_user.password:
                self.set_secure_cookie('username', has_user.user_name, expires_days=365)
                self.set_secure_cookie('email', has_user.email, expires_days=365)
                self.set_secure_cookie('password', password, expires_days=365)
                self.write(json.dumps("OK"))
                return
            else:
                self.write(json.dumps("权限验证失败或帐户不可用！"))
                return
        else:
            self.write(json.dumps("验证码填写错误或用户不存在！"))
            return


class Logout(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('%s/admin/login' % BASE_URL)


class Forbidden(BaseHandler):
    def get(self):
        self.write('Forbidden page')


class FileUpload(BaseHandler):
    @authorized()
    def post(self):
        self.set_header('Content-Type', 'text/html')
        rspd = {'status': 201, 'msg': 'ok'}
        max_size = 10240000  # 10MB
        fileupload = self.request.files['imgFile']
        if fileupload:
            myfile = fileupload[0]
            if not myfile['filename']:
                self.write(json.dumps(
                    {'error': 1, 'message': u'请选择要上传的文件'}
                ))
                return

            # if myfile.size > max_size:
            #     self.write(json.dumps(
            #         { 'error': 1, 'message': u'上传的文件大小不能超过 10 MB'}
            #     ))
            #     return

            file_type = myfile['filename'].split('.')[-1].lower()
            file_name = str(int(time.time() * 1000))
            mime_type = myfile['content_type']
            encoding = None

            # 缩放图片
            try:
                if file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    new_file_name = "%s-thumb.%s" % (file_name, file_type)
                    img_data = Thumbnail(StringIO.StringIO(myfile['body'])).thumb((100, 100))
                    put_storage(file_name=new_file_name, data=img_data, expires='365',
                                con_type=mime_type, encoding=encoding)
                    #im = Image.open(StringIO.StringIO(myfile['body']))
                    # im.show()
                    #width, height = im.size
                    #if width > 750:
                    #    ratio = 1.0 * height / width
                    #    new_height = int(750 * ratio)
                    #    new_size = (750, new_height)
                    #    out = im.resize(new_size, Image.ANTIALIAS)
                    #    myfile['body'] = out.toString('jpeg', 'RGB')
                    #    file_type = 'jpg'
                    #    print 750, new_height
                    #    new_file_name = "%s-thumb.%s" % (str(int(time.time())), file_type)
                    #else:
                    #    pass
                else:
                    pass
            except:
                pass

            try:
                new_file_name = "%s.%s" % (file_name, file_type)
                attachment_url = put_storage(file_name=new_file_name, data=myfile['body'], expires='365',
                                             con_type=mime_type, encoding=encoding)
            except:
                attachment_url = ''

            if attachment_url:
                rspd['status'] = 200
                rspd['error'] = 0
                rspd['filename'] = myfile['filename']
                rspd['url'] = attachment_url
            else:
                rspd['status'] = 500
                rspd['error'] = 1
                rspd['message'] = 'put_saestorage error, try it again.'
        else:
            rspd['message'] = 'No file uploaded'
        self.write(json.dumps(rspd))
        return


class FileManager(BaseHandler):
    @authorized()
    def get(self):
        file_list = get_storage_list()

        upload = {
            "moveup_dir_path": "",
            "current_dir_path": "/stor-stub/attachment/",
            "current_url": BASE_URL + "/stor-stub/attachment/",
            "file_list": [],
        }

        for dirfile in file_list:
            filesize = dirfile['length']
            filetype = dirfile['name'].split('.')[-1].lower()
            filename = dirfile['name']
            datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dirfile['datetime']))
            if re.match('gif|jpg|jpeg|png|bmp', filetype):
                is_photo = True
            else:
                is_photo = False
            file_list = {
                "is_dir": False,
                "has_file": False,
                "filesize": filesize,
                "dir_path": "/stor-stub/attachment/",
                "is_photo": is_photo,
                "filetype": filetype,
                "filename": filename,
                "datetime": datetime,
            }
            upload["file_list"].append(file_list)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(upload))
        return


class BlogSetting(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting.html', {
            'title': "站点信息",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        value = self.get_argument("SITE_TITLE", '')
        if value:
            setAttr('SITE_TITLE', value)
        value = self.get_argument("SITE_TITLE2", '')
        if value:
            setAttr('SITE_TITLE2', value)

        value = self.get_argument("SITE_SUB_TITLE", '')
        if value:
            setAttr('SITE_SUB_TITLE', value)

        value = self.get_argument("KEYWORDS", '')
        if value:
            setAttr('KEYWORDS', value)

        value = self.get_argument("SITE_DECR", '')
        if value:
            setAttr('SITE_DECR', value)

        value = self.get_argument("ADMIN_NAME", '')
        if value:
            setAttr('ADMIN_NAME', value)

        value = self.get_argument("MOVE_SECRET", '')
        if value:
            setAttr('MOVE_SECRET', value)

        value = self.get_argument("NOTICE_MAIL", '')
        if value:
            setAttr('NOTICE_MAIL', value)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting2(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting2.html', {
            'title': "邮箱配置",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        value = self.get_argument("MAIL_FROM", '')
        if value:
            setAttr('MAIL_FROM', value)

        value = self.get_argument("MAIL_KEY", '')
        if value:
            setAttr('MAIL_KEY', value)

        value = self.get_argument("MAIL_SMTP", '')
        if value:
            setAttr('MAIL_SMTP', value)

        value = self.get_argument("MAIL_PORT", '')
        if value:
            setAttr('MAIL_PORT', value)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting3(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting3.html', {
            'title': "详细参数",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        # 文章相关
        EACH_PAGE_POST_NUM = self.get_argument("EACH_PAGE_POST_NUM", '')
        if EACH_PAGE_POST_NUM:
            setAttr('EACH_PAGE_POST_NUM', EACH_PAGE_POST_NUM)

        SHORTEN_CONTENT_WORDS = self.get_argument("SHORTEN_CONTENT_WORDS", '')
        if SHORTEN_CONTENT_WORDS:
            setAttr('SHORTEN_CONTENT_WORDS', SHORTEN_CONTENT_WORDS)

        DESCRIPTION_CUT_WORDS = self.get_argument("DESCRIPTION_CUT_WORDS", '')
        if DESCRIPTION_CUT_WORDS:
            setAttr('DESCRIPTION_CUT_WORDS', DESCRIPTION_CUT_WORDS)

        RELATIVE_POST_NUM = self.get_argument("RELATIVE_POST_NUM", '')
        if RELATIVE_POST_NUM:
            setAttr('RELATIVE_POST_NUM', RELATIVE_POST_NUM)

        # 评论相关
        EACH_PAGE_COMMENT_NUM = self.get_argument("EACH_PAGE_COMMENT_NUM", '')
        if EACH_PAGE_COMMENT_NUM:
            setAttr('EACH_PAGE_COMMENT_NUM', EACH_PAGE_COMMENT_NUM)

        RECENT_COMMENT_NUM = self.get_argument("RECENT_COMMENT_NUM", '')
        if RECENT_COMMENT_NUM:
            setAttr('RECENT_COMMENT_NUM', RECENT_COMMENT_NUM)

        RECENT_COMMENT_CUT_WORDS = self.get_argument("RECENT_COMMENT_CUT_WORDS", '')
        if RECENT_COMMENT_CUT_WORDS:
            setAttr('RECENT_COMMENT_CUT_WORDS', RECENT_COMMENT_CUT_WORDS)

        MAX_COMMENT_NUM_A_DAY = self.get_argument("MAX_COMMENT_NUM_A_DAY", '')
        if MAX_COMMENT_NUM_A_DAY:
            setAttr('MAX_COMMENT_NUM_A_DAY', MAX_COMMENT_NUM_A_DAY)

        COMMENT_DEFAULT_VISIBLE = self.get_argument("COMMENT_DEFAULT_VISIBLE", '')
        if COMMENT_DEFAULT_VISIBLE:
            setAttr('COMMENT_DEFAULT_VISIBLE', COMMENT_DEFAULT_VISIBLE)

        # 其他设置
        LINK_NUM = self.get_argument("LINK_NUM", '')
        if LINK_NUM:
            setAttr('LINK_NUM', LINK_NUM)

        HOT_TAGS_NUM = self.get_argument("HOT_TAGS_NUM", '')
        if HOT_TAGS_NUM:
            setAttr('HOT_TAGS_NUM', HOT_TAGS_NUM)

        MAX_ARCHIVES_NUM = self.get_argument("MAX_ARCHIVES_NUM", '')
        if MAX_ARCHIVES_NUM:
            setAttr('MAX_ARCHIVES_NUM', MAX_ARCHIVES_NUM)

        clear_all_cache()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


class BlogSetting4(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting4.html', {
            'title': "广告统计",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        ANALYTICS_CODE = self.get_argument("ANALYTICS_CODE", '')
        if ANALYTICS_CODE:
            setAttr('ANALYTICS_CODE', ANALYTICS_CODE)

        ADSENSE_CODE1 = self.get_argument("ADSENSE_CODE1", '')
        if ADSENSE_CODE1:
            setAttr('ADSENSE_CODE1', ADSENSE_CODE1)

        ADSENSE_CODE2 = self.get_argument("ADSENSE_CODE2", '')
        if ADSENSE_CODE2:
            setAttr('ADSENSE_CODE2', ADSENSE_CODE2)

        clear_all_cache()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


# 后台相关
class BlogSetting5(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting5.html', {
            'title': "详细参数",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        ADMIN_CATEGORY_NUM = self.get_argument("ADMIN_CATEGORY_NUM", '')
        if ADMIN_CATEGORY_NUM:
            setAttr('ADMIN_CATEGORY_NUM', ADMIN_CATEGORY_NUM)

        ADMIN_POST_NUM = self.get_argument("ADMIN_POST_NUM", '')
        if ADMIN_POST_NUM:
            setAttr('ADMIN_POST_NUM', ADMIN_POST_NUM)

        ADMIN_COMMENT_NUM = self.get_argument("ADMIN_COMMENT_NUM", '')
        if ADMIN_COMMENT_NUM:
            setAttr('ADMIN_COMMENT_NUM', ADMIN_COMMENT_NUM)

        ADMIN_USER_NUM = self.get_argument("ADMIN_USER_NUM", '')
        if ADMIN_USER_NUM:
            setAttr('ADMIN_USER_NUM', ADMIN_USER_NUM)

        ADMIN_LINK_NUM = self.get_argument("ADMIN_LINK_NUM", '')
        if ADMIN_LINK_NUM:
            setAttr('ADMIN_LINK_NUM', ADMIN_LINK_NUM)

        clear_cache_by_pathlist(['/'])

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps("OK"))
        return


# TODO KVDB 管理
class KVDBAdmin(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_kvdb.html', {
            'title': "KVDB 管理",
        }, layout='_layout_admin.html')

    @authorized()
    def post(self):
        self.redirect('%s/admin/kvdb' % BASE_URL)
        return


class FlushData(BaseHandler):
    @authorized()
    def post(self):
        act = self.get_argument("act", '')
        if act == 'flush':
            from deploy.create_db import flush_all_data
            flush_all_data()
            clear_all_cache()
            clearAllKVDB()
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return
        elif act == 'flushcache':
            clear_all_cache()
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps("OK"))
            return


class PingRPCTask(BaseHandler):
    def get(self):
        for n in range(len(XML_RPC_ENDPOINTS)):
            add_task('default', '%s/task/pingrpc/%d' % (BASE_URL, n))
        self.write(str(time.time()))

    post = get


class PingRPC(BaseHandler):
    def get(self, n=0):
        import urllib2

        pingstr = self.render('rpc.xml', {'article_id': Posts.get_max_id()})

        headers = {
            'User-Agent': 'request',
            'Content-Type': 'text/xml',
            'Content-length': str(len(pingstr))
        }

        req = urllib2.Request(
            url=XML_RPC_ENDPOINTS[int(n)],
            headers=headers,
            data=pingstr,
        )
        try:
            content = urllib2.urlopen(req).read()
            tip = 'Ping ok' + content
        except:
            tip = 'ping erro'

        self.write(str(time.time()) + ": " + tip)
        #add_task('default', '%s/task/sendmail'%BASE_URL, urlencode({'subject': tip, 'content': tip + " " + str(n)}))

    post = get


class SendMail(BaseHandler):
    def post(self):
        subject = self.get_argument("subject", '')
        content = self.get_argument("content", '')

        if subject and content:
            sendEmail(subject, content, getAttr('NOTICE_MAIL'))


# 初始化一些参数
def Init():
    setAttr('SITE_TITLE', SITE_TITLE)
    setAttr('SITE_TITLE2', SITE_TITLE2)
    setAttr('SITE_SUB_TITLE', SITE_SUB_TITLE)
    setAttr('KEYWORDS', KEYWORDS)
    setAttr('SITE_DECR', SITE_DECR)
    setAttr('ADMIN_NAME', ADMIN_NAME)
    setAttr('NOTICE_MAIL', NOTICE_MAIL)
    setAttr('MOVE_SECRET', MOVE_SECRET)

    setAttr('MAIL_FROM', MAIL_FROM)
    setAttr('MAIL_KEY', MAIL_KEY)
    setAttr('MAIL_SMTP', MAIL_SMTP)
    setAttr('MAIL_PORT', MAIL_PORT)

    setAttr('EACH_PAGE_POST_NUM', EACH_PAGE_POST_NUM)
    setAttr('EACH_PAGE_COMMENT_NUM', EACH_PAGE_COMMENT_NUM)
    setAttr('RELATIVE_POST_NUM', RELATIVE_POST_NUM)
    setAttr('SHORTEN_CONTENT_WORDS', SHORTEN_CONTENT_WORDS)
    setAttr('DESCRIPTION_CUT_WORDS', DESCRIPTION_CUT_WORDS)

    setAttr('RECENT_COMMENT_NUM', RECENT_COMMENT_NUM)
    setAttr('RECENT_COMMENT_CUT_WORDS', RECENT_COMMENT_CUT_WORDS)
    setAttr('MAX_COMMENT_NUM_A_DAY', MAX_COMMENT_NUM_A_DAY)
    setAttr('COMMENT_DEFAULT_VISIBLE', COMMENT_DEFAULT_VISIBLE)

    setAttr('LINK_NUM', LINK_NUM)
    setAttr('HOT_TAGS_NUM', HOT_TAGS_NUM)
    setAttr('MAX_ARCHIVES_NUM', MAX_ARCHIVES_NUM)

    setAttr('ANALYTICS_CODE', ANALYTICS_CODE)
    setAttr('ADSENSE_CODE1', ADSENSE_CODE1)
    setAttr('ADSENSE_CODE2', ADSENSE_CODE2)

    setAttr('ADMIN_CATEGORY_NUM', ADMIN_CATEGORY_NUM)
    setAttr('ADMIN_POST_NUM', ADMIN_POST_NUM)
    setAttr('ADMIN_COMMENT_NUM', ADMIN_COMMENT_NUM)
    setAttr('ADMIN_USER_NUM', ADMIN_USER_NUM)
    setAttr('ADMIN_LINK_NUM', ADMIN_LINK_NUM)


class Install(BaseHandler):
    def get(self):
        Init()
        self.echo('admin_install.html')
        # try:
        #     self.write('如果出现错误请尝试刷新本页。')
        #     has_user = User.check_has_user()
        #     if has_user:
        #         self.write('博客已经成功安装了，你可以直接 <a href="/admin/flushdata">清空网站数据</a>')
        #     else:
        #         self.write('博客数据库已经建立，现在就去 <a href="/admin/">设置一个管理员帐号</a>')
        # except:
        #     try:
        #         MyData.creat_table()
        #         Init()  # 初始化系统参数
        #     except:
        #         pass
        #     self.write('博客已经成功安装了，现在就去 <a href="/admin/">设置一个管理员帐号</a>')

    def post(self):
        pass


class GetCaptcha(BaseHandler):
    def get(self):
        text = random_int(4)
        self.set_secure_cookie("captcha", text)

        strIO = Recaptcha(text)

        # ,mimetype='image/png'
        self.set_header("Content-Type", "image/png")
        self.write(strIO.read())
        return


class NotFoundPage(BaseHandler):
    def get(self):
        self.set_status(404)
        self.echo('error.html', {
            'page': '404',
            'title': "Can't find out this URL",
            'h2': 'Oh, my god!',
            'msg': '<script type="text/javascript" src="http://www.qq.com/404/search_children.js?edition=small" charset="utf-8"></script>'
        })

#####
urls = [
    (r"/admin/", HomePage),
    (r"/admin/login", Login),
    (r"/admin/logout", Logout),
    (r"/admin/403", Forbidden),
    # 文件上传及管理
    (r"/admin/fileupload", FileUpload),
    (r"/admin/filelist", FileManager),
    (r"/admin/setting", BlogSetting),
    (r"/admin/setting2", BlogSetting2),
    (r"/admin/setting3", BlogSetting3),
    (r"/admin/setting4", BlogSetting4),
    (r"/admin/setting5", BlogSetting5), # 后台设置
    (r"/admin/kvdb", KVDBAdmin),
    (r"/admin/flushdata", FlushData),
    (r"/task/pingrpctask", PingRPCTask),
    (r"/task/pingrpc/(\d+)", PingRPC),
    (r"/task/sendmail", SendMail),
    (r"/captcha/", GetCaptcha),
    (r"/install", Install),
    (r".*", NotFoundPage)
]
