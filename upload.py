# -*- coding:utf-8 -*-
import json
import os
import glob
import re
import time
from common import BaseHandler, authorized

__author__ = 'baitao.ji'

udir = os.path.join(os.path.dirname(__file__))[0:-7] + "static/attached"


class UploadHandler(BaseHandler):
    @authorized
    def get(self):
        upload = {
            "moveup_dir_path": "",
            "current_dir_path": "",
            "current_url": "/static/attached/",
            "file_list": [],
        }

        for dirfile in glob.glob(udir + '/*'):
            filesize = os.path.getsize(dirfile)
        filetype = os.path.splitext(dirfile)[-1].lower()
        filename = os.path.basename(dirfile)
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(dirfile)))
        if re.match('\.gif|\.jpg|\.jpeg|\.png|\.bmp', filetype):
            is_photo = True
        else:
            is_photo = False
        file_list = {
            "is_dir": False,
            "has_file": False,
            "filesize": filesize,
            "dir_path": "",
            "is_photo": is_photo,
            "filetype": filetype,
            "filename": filename,
            "datetime": datetime,
        }
        upload["file_list"].append(file_list)
        upload = json.dumps(upload)
        self.write(upload)

    @authorized
    def post(self):
        if self.request.files:
            for f in self.request.files["imgFile"]:
                try:
                    rawname = f['filename']
                    rename = str(int(time.time())) + '.' + rawname.split('.').pop()
                    dstname = udir + "/" + rename
                    fbody = f["body"]
                    (lambda f, d: (f.write(d), f.close()))(open(dstname, 'wb'), fbody)
                    info = {
                        "error": 0,
                        "url": "/static/attached/" + rename
                    }
                except Exception, ex:
                    info = {
                        "error": 1,
                        #"message" : "文件上传失败！"
                        "message": str(ex)
                    }
            else:
                info = {
                    "error": 1,
                    "message": "您没有上传任何文件！"
                }

        info = json.dumps(info)
        self.write(info)