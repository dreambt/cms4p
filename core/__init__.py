# -*- coding: utf-8 -*-
import datetime
import decimal

_author__ = 'baitao.ji'


def dthandler(obj):
    """
    解决 datetime 无法序列化为 json 的问题
    json.dumps(result, default=dthandler)
    :param obj:
    :return:
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        return (datetime.datetime.min + obj).time().isoformat()
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    else:
        raise TypeError('%r is not JSON serializable' % obj)