#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import os
from bs4 import BeautifulSoup
import HTMLParser
from datetime import datetime



def stripHtmlText(text):
    # remove &nbsp; from text
    html_parser = HTMLParser.HTMLParser()
    unescaped = html_parser.unescape(text)
    unescaped = html_parser.unescape(unescaped)
    return unescaped


def pick(source, keys, base=None):
    res = {}
    for key in keys:
        if key in source:
            res[key] = source[key]
    if not base is None:
        return base.update(res)
    return res


def config_from_env(prefix='FARM_'):
    """
    Load all environment variables prefixed by `prefix`

    :param config: load config from config.py
    :param prefix: prefix of env vars
    :returns: a configuration dict
    """
    l = len(prefix)
    conf = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
            try:
                v = ast.literal_eval(v)
            except (ValueError, SyntaxError):
                pass
            conf[k[l:]] = v
    return conf
