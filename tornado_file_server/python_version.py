# -*- coding: utf-8 -*-
"""
check python version

author: zhaoyafei0210@gmail.com
github: https://github.com/walkoncross/tornado-file-server
"""

import sys


def is_python3():
    """is_python3

    Returns:
        boo: is python3 or not
    """
    return (sys.version_info.major > 2)
