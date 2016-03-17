#! usr/bin/env python
# encoding: utf-8

import os

logdir = os.path.abspath(os.path.join(__file__, '../../logs'))
if not os.path.exists(logdir):
    os.makedirs(logdir)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s.%(msecs)d] %(levelname)s [%(module)s:%(funcName)s:%(lineno)d]- %(message)s',
            'datefmt' : "%y/%m/%d %H:%M:%S",
        },
    },

    'handlers': {

        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': logdir + "/default.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'delay': True,
            'formatter':'standard',
        },
        # 'celeryTasks': {
        #     'level':'DEBUG',
        #     'class':'logging.handlers.TimedRotatingFileHandler',
        #     'filename': logdir + "/celeryTasks/celeryTasks.log",
        #     'when': 'midnight',
        #     'interval': 1,
        #     'backupCount': 30,
        #     'delay': False,
        #     'formatter':'standard',
        # },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },

        'request_handler': {
            'level':'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename':logdir+"/request.log",
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'delay': True,
            'formatter':'standard',
        },

    },
    'loggers': {

        'request': {
            'handlers': ['request_handler', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },

    }
}

