# -*- coding:utf-8 -*-
import random

__author__ = 'baitao.ji'


def generate_random(length=8):
    """Generate random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])