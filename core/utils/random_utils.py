# -*- coding: utf-8 -*-
_author__ = 'baitao.ji'

import string
import random


def random_string(length=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    """Generate random string."""
    #''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(length)))
    #''.join(random.sample('zAyBxCwDvEuFtGsHrIqJpKoLnMmNlOkPjQiRhSgTfUeVdWcXbYaZ1928374650', 16))
    #''.join(random.choice(string.letters + string.digits) for x in range(length))
    return ''.join(random.choice(chars) for x in range(length))


def random_ascii(length=6):
    """Generate random ascii."""
    return random_string(length, string.ascii_letters)


def random_int(length=6):
    """Generate random number."""
    # return ''.join([str(random.randint(0, 9)) for i in range(length)])
    return random_string(length, string.digits)


if __name__ == '__main__':
    print random_string(8)
    print random_int()