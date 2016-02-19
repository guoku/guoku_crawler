#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import os


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
