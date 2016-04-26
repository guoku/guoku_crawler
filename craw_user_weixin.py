from __future__ import absolute_import
import argparse
from guoku_crawler.article import crawl_user_weixin_articles_by_authorized_user_id

parser = argparse.ArgumentParser(description='Craw Weixin Articles for Authorized User by Authorized user id')

parser.add_argument('ids', metavar='N', type=int, nargs='+',
                   help='id list for authorized ids')

args = parser.parse_args()

for authorized_user_id in args.ids:
    print 'print authorized_user_id for : %s' %authorized_user_id
    print '*' * 80
    crawl_user_weixin_articles_by_authorized_user_id(authorized_user_id)
