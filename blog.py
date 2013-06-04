# -*- coding: utf-8 -*-

import json

from hashlib import md5
from time import time
from urlparse import unquote

from setting import *

from common import BaseHandler, unquoted_unicode, safe_encode, pagecache, clear_cache_by_pathlist, client_cache, get_count, increment, getAttr

from model import Article, Comment, Link, Category, Tag, Archive

class HomePage(BaseHandler):
    @pagecache()
    def get(self):
        try:
            objs = Article.get_post_for_homepage()
        except:
            self.redirect('/install')
            return
        if objs:
            fromid = objs[0].id
            endid = objs[-1].id
        else:
            fromid = endid = ''

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = Article.count_all()
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1

        output = self.render('index.html', {
            'title': "%s - %s" % (getAttr('SITE_TITLE'), getAttr('SITE_SUB_TITLE')),
            'keywords': getAttr('KEYWORDS'),
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': all_page,
            'listtype': 'index',
            'fromid': fromid,
            'endid': endid,
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
        }, layout='_layout.html')
        self.write(output)
        return output


class IndexPage(BaseHandler):
    @pagecache('post_list_index', getAttr('PAGE_CACHE_TIME'), lambda self, direction, page, base_id: page)
    def get(self, direction='next', page='2', base_id='1'):
        if page == '1':
            self.redirect(BASE_URL)
            return
        objs = Article.get_page_posts(direction, page, base_id)
        if objs:
            if direction == 'prev':
                objs.reverse()
            fromid = objs[0].id
            endid = objs[-1].id
        else:
            fromid = endid = ''

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = Article.count_all()
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1
        output = self.render('default.html', {
            'title': "%s - %s | Part %s" % (getAttr('SITE_TITLE'), getAttr('SITE_SUB_TITLE'), page),
            'keywords': getAttr('KEYWORDS'),
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': int(page),
            'allpage': all_page,
            'listtype': 'index',
            'fromid': fromid,
            'endid': endid,
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
        }, layout='_layout.html')
        self.write(output)
        return output


class PostDetailShort(BaseHandler):
    @client_cache(600, 'public')
    def get(self, id=''):
        obj = Article.get_article_by_id_simple(id)
        if obj:
            self.redirect('%s/topic/%d/%s' % (BASE_URL, obj.id, obj.title), 301)
            return
        else:
            self.redirect(BASE_URL)


class PostDetail(BaseHandler):
    @pagecache('post', getAttr('PAGE_CACHE_TIME'), lambda self, id, title: id)
    def get(self, id='', title=''):
        tmpl = ''
        obj = Article.get_article_by_id_detail(id)
        if not obj:
            self.redirect(BASE_URL)
            return
            #redirect to right title
        try:
            title = unquote(title).decode('utf-8')
        except:
            pass
        if title != obj.slug:
            self.redirect(obj.absolute_url, 301)
            return
            #
        if obj.password and THEME == 'default':
            rp = self.get_secure_cookie("rp%s" % id, '')
            if rp != obj.password:
                tmpl = '_pw'
        elif obj.password and getAttr('BLOG_PSW_SUPPORT'):
            rp = self.get_secure_cookie("rp%s" % id, '')
            print 'rp===%s' % (str(rp))
            if rp != obj.password:
                tmpl = '_pw'

        keyname = 'pv_%s' % (str(id))
        increment(keyname)
        self.set_secure_cookie(keyname, '1', expires_days=1)
        self.set_header("Last-Modified", obj.last_modified)

        template_prefix = 'post'
        if obj.category == '-':
            template_prefix = 'page'

        output = self.render(template_prefix+'%s.html' % tmpl, {
            'title': "%s - %s" % (obj.title, getAttr('SITE_TITLE')),
            'keywords': obj.keywords,
            'description': obj.description,
            'obj': obj,
            'cobjs': obj.coms,
            'postdetail': 'postdetail',
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': 10,
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'hits': get_count(keyname),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
            'listtype': '',
        }, layout='_layout.html')
        self.write(output)

        if obj.password and getAttr('BLOG_PSW_SUPPORT'):
            return output
        elif obj.password and THEME == 'default':
            return
        else:
            return output

    def post(self, id='', title=''):
        action = self.get_argument("act")

        if action == 'inputpw':
            wrn = self.get_secure_cookie("wrpw")
            if wrn is not None and int(wrn) >= 10:
                self.write('403')
                return

            pw = self.get_argument("pw", '')
            pobj = Article.get_article_by_id_simple(id)
            if pw:
                if pobj.password == pw:
                    clear_cache_by_pathlist(['post:%s' % id])
                    self.set_secure_cookie("rp%s" % id, pobj.password, expires_days=1)
                else:
                    self.set_secure_cookie("wrpw", str(int(wrn) + 1), expires_days=1)
            else:
                self.set_secure_cookie("wrpw", str(int(wrn) + 1), expires_days=1)

            self.redirect('%s/topic/%d/%s' % (BASE_URL, pobj.id, pobj.title))
            return

        self.set_header('Content-Type', 'application/json')
        rspd = {'status': 201, 'msg': 'ok'}

        if action == 'readmorecomment':
            fromid = self.get_argument("fromid", '')
            all_num = int(self.get_argument("allnum", 0))
            each_page_comment_num = getAttr('EACH_PAGE_COMMENT_NUM')
            showed_num = int(self.get_argument("showednum", each_page_comment_num))
            if fromid:
                rspd['status'] = 200
                if (all_num - showed_num) >= each_page_comment_num:
                    limit = each_page_comment_num
                else:
                    limit = all_num - showed_num
                cobjs = Comment.get_post_page_comments_by_id(id, fromid, limit)
                rspd['commentstr'] = self.render('comments.html', {'cobjs': cobjs})
                rspd['lavenum'] = all_num - showed_num - limit
                self.write(json.dumps(rspd))
            return

        # 评论次数限制不好使
        usercomnum = self.get_secure_cookie("usercomnum")
        if usercomnum is not None and int(usercomnum) > getAttr('MAX_COMMENT_NUM_A_DAY'):
            rspd = {'status': 403, 'msg': '403: Forbidden'}
            self.write(json.dumps(rspd))
            return
        else:
            usercomnum = 0

        try:
            post_dic = {
                'author': self.get_argument("author"),
                'email': self.get_argument("email", ''),
                'content': safe_encode(self.get_argument("comment").replace('\r', '\n')),
                'url': self.get_argument("url", ''),
                'postid': self.get_argument("postid"),
                'add_time': int(time()),
                'toid': self.get_argument("toid", ''),
                'visible': getAttr('COMMENT_DEFAULT_VISIBLE')
            }
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误：请检查你提交的数据是否正确！'
            self.write(json.dumps(rspd))
            return

        pobj = Article.get_article_by_id_simple(id)
        if pobj and not pobj.closecomment:
            cobjid = Comment.add_new_comment(post_dic)
            if cobjid:
                Article.update_post_comment(pobj.comment_num + 1, id)
                self.set_secure_cookie("usercomnum", str(int(usercomnum) + 1), expires_days=1)
                rspd['status'] = 200
                rspd['msg'] = '恭喜您，已成功提交评论！'

                rspd['msg'] = self.render('comment.html', {
                    'postid': id,
                    'cobjid': cobjid,
                    'gravatar': 'http://www.gravatar.com/avatar/%s' % md5(post_dic['email']).hexdigest(),
                    'url': post_dic['url'],
                    'author': post_dic['author'],
                    'add_time': int(time()),
                    'visible': post_dic['visible'],
                    'content': post_dic['content'],
                })

                clear_cache_by_pathlist(['/', 'post:%s' % id])

                #send mail
                if not debug:
                    try:
                        NOTICE_MAIL = getAttr('NOTICE_MAIL')
                        if NOTICE_MAIL:
                            tolist = [NOTICE_MAIL]
                        else:
                            tolist = []
                        if post_dic['toid']:
                            tcomment = Comment.get_comment_by_id(post_dic['toid'])
                            if tcomment and tcomment.email:
                                tolist.append(tcomment.email)
                        commenturl = "%s/t/%s#r%s" % (BASE_URL, str(pobj.id), str(cobjid))
                        m_subject = u'有人回复您在 《%s》 里的评论 %s' % ( pobj.title, str(cobjid))
                        m_html = u'这是一封提醒邮件（请勿直接回复）： %s ，请尽快处理： %s' % (m_subject, commenturl)

                        if tolist:
                            import sae.mail

                            sae.mail.send_mail(','.join(tolist), m_subject, m_html,
                                               (getAttr('MAIL_SMTP'), int(getAttr('MAIL_PORT')), getAttr('MAIL_FROM'),
                                                getAttr('MAIL_KEY'), True))

                    except:
                        pass
            else:
                rspd['msg'] = '保存评论失败！'
        else:
            rspd['msg'] = '当前文章禁止评论！'
        self.write(json.dumps(rspd))


class CategoryDetailShort(BaseHandler):
    @client_cache(3600, 'public')
    def get(self, id=''):
        obj = Category.get_cat_by_id(id)
        if obj:
            self.redirect('%s/category/%s' % (BASE_URL, obj.name), 301)
            return
        else:
            self.redirect(BASE_URL)


class CategoryDetail(BaseHandler):
    @pagecache('cat', getAttr('PAGE_CACHE_TIME'), lambda self, name: name)
    def get(self, name=''):
        objs = Category.get_cat_page_posts(name, 1)
        catobj = Category.get_by_name(name)
        show_type = self.get_argument('type', 'default')

        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = catobj.id_num
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1

        output = self.render(show_type+'.html', {
            'title': "%s - %s" % (catobj.name, getAttr('SITE_TITLE')),
            'keywords': catobj.name,
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': all_page,
            'listtype': 'cat',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
        }, layout='_layout.html')
        self.write(output)
        return output


class ArchiveDetail(BaseHandler):
    @pagecache('archive', getAttr('PAGE_CACHE_TIME'), lambda self, name: name)
    def get(self, name=''):
        if not name:
            print 'ArchiveDetail name null'
            name = Archive.get_latest_archive_name()

        objs = Archive.get_archive_page_posts(name, 1)

        archiveobj = Archive.get_archive_by_name(name)
        if archiveobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = archiveobj.id_num
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1

        output = self.render('index.html', {
            'title': "%s - %s" % (archiveobj.name, getAttr('SITE_TITLE')),
            'keywords': archiveobj.name,
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': all_page,
            'listtype': 'archive',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
        }, layout='_layout.html')
        self.write(output)
        return output


class TagDetail(BaseHandler):
    @pagecache()
    def get(self, name=''):
        objs = Tag.get_tag_page_posts(name, 1)

        catobj = Tag.get_tag_by_name(name)
        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = catobj.id_num
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1

        output = self.render('list.html', {
            'title': "%s - %s" % (catobj.name, getAttr('SITE_TITLE')),
            'keywords': catobj.name,
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': all_page,
            'listtype': 'tag',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
        }, layout='_layout.html')
        self.write(output)
        return output


class ArticleList(BaseHandler):
    @pagecache('post_list_tag', getAttr('PAGE_CACHE_TIME'), lambda self, list_type, direction, page, name: "%s_%s" % (name, page))
    def get(self, list_type='', direction='next', page='1', name=''):
        if list_type == 'cat':
            objs = Category.get_cat_page_posts(name, page)
            catobj = Category.get_by_name(name)
        elif list_type == 'tag':
            objs = Tag.get_tag_page_posts(name, page)
            catobj = Tag.get_tag_by_name(name)
        elif list_type == 'archive':
            objs = Archive.get_archive_page_posts(name, page)
            catobj = Archive.get_archive_by_name(name)

        show_type = self.get_argument('type', 'default')

        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        each_page_post_num = int(getAttr('EACH_PAGE_POST_NUM'))
        all_post = catobj.id_num
        all_page = all_post / each_page_post_num
        if all_post % each_page_post_num:
            all_page += 1

        output = self.render(show_type+'.html', {
            'title': "%s - %s | Part %s" % ( catobj.name, getAttr('SITE_TITLE'), page),
            'keywords': catobj.name,
            'description': getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': int(page),
            'allpage': all_page,
            'listtype': list_type,
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links': Link.get_all_links(),
            'Totalblog': get_count('Totalblog', NUM_SHARDS, 0),
        }, layout='_layout.html')
        self.write(output)
        return output


class Robots(BaseHandler):
    def get(self):
        self.echo('robots.txt', {'cats': Category.get_by_id()})


class Feed(BaseHandler):
    def get(self):
        posts = Article.get_post_for_homepage()
        output = self.render('index.xml', {
            'posts': posts,
            'site_updated': Article.get_last_post_add_time(),
        })
        self.set_header('Content-Type', 'application/atom+xml')
        self.write(output)


class Sitemap(BaseHandler):
    def get(self, id=''):
        self.set_header('Content-Type', 'text/xml')
        self.echo('sitemap.html', {'sitemapstr': Category.get_sitemap_by_id(id), 'id': id})


class Attachment(BaseHandler):
    def get(self, name):
        self.redirect('http://%s-%s.stor.sinaapp.com/%s' % (APP_NAME, STORAGE_DOMAIN_NAME, unquoted_unicode(name)), 301)
        return

########
urls = [
    (r"/", HomePage),
    (r"/robots.txt", Robots),
    (r"/feed", Feed),
    (r"/index.xml", Feed),
    # 文章
    (r"/t/(\d+)$", PostDetailShort),
    (r"/topic/(\d+)/(.*)$", PostDetail),
    (r"/index_(prev|next)_page/(\d+)/(\d+)/$", IndexPage),
    # 分类
    (r"/c/(\d+)$", CategoryDetailShort),
    (r"/category/(.+)/$", CategoryDetail),

    (r"/tag/(.+)/$", TagDetail),
    (r"/archive/", ArchiveDetail),
    (r"/archive/(.+)/$", ArchiveDetail),
    (r"/(cat|tag|archive)_(prev|next)_page/(\d+)/(.+)/$", ArticleList),
    (r"/sitemap_(\d+)\.xml$", Sitemap),
    (r"/attachment/(.+)$", Attachment),
]
