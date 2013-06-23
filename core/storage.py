# -*- coding: utf-8 -*-
from sae.storage import Bucket
from setting import DEFAULT_BUCKET

_author__ = 'baitao.ji'

bucket = Bucket(DEFAULT_BUCKET)


def put_storage(file_name='', data='', expires='365', con_type=None, encoding=None, domain_name=DEFAULT_BUCKET):
    """
    上传文件
    :param file_name: 文件名
    :param data: 上传时间
    :param expires:
    :param con_type:
    :param encoding:
    :param domain_name:
    :return: 文件访问地址
    """
    bucket.put_object(file_name, data)
    return bucket.generate_url(file_name)
    #s = sae.storage.Client()
    #ob = sae.storage.Object(data=data, cache_control='access plus %s day' % expires, content_type=con_type,
    #                        content_encoding=encoding)
    #return s.put(domain_name, str(datetime.now().strftime("%Y%m") + "/" + file_name), ob)
    #return s.put(domain_name, file_name, ob)


def get_storage_list(domain_name=DEFAULT_BUCKET):
    """
    获取文件列表
    :param domain_name:
    :return: 文件列表
    """
    #s = sae.storage.Client()
    #filelist = s.list(domain_name)
    filelist = bucket.list()
    #total_count = len(filelist)
    return filelist