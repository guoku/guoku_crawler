#!/usr/bin/env python


import ConfigParser
import os

from fabric.api import *
from fabric.context_managers import *
from fabric.contrib.project import rsync_project

Config = ConfigParser.ConfigParser()
Config.read('config.ini')

root_dir = os.path.join(os.getcwd(), '..')

env.hosts = ['114.113.154.49']

env.user = Config.get('global', 'user')
#env.key = os.path.join(root_dir, Config.get('global', 'key'))
env.password = 'jessie1@#'

env.local_root = os.path.join(root_dir, Config.get('local', 'project_dir'))
env.project_root = Config.get('server', 'project_dir')

def update_code():
    local('git pull origin dev')


@parallel
def upload_code():
    rsync_project(
            remote_dir = env.project_root,
            local_dir = env.local_root,
            delete = True,
            extra_opts = "--password-file='guoku.pass' "
        )

# script_dir = Config.get('server', 'script_dir')
#
# def reload_gunicorn():
# 	with cd(script_dir):
# 		sudo('/bin/bash ./gunicorn reload')

def upload():
    execute(upload_code)

# def reload_test():
#     execute(reload_gunicorn)
