#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import gc
import unicodedata

from bs4 import BeautifulSoup


tbl = dict.fromkeys(i for i in range(sys.maxunicode) if
                    unicodedata.category(chr(i)).startswith('P'))


def parse_article_link(result_json):
    article_link_list = []
    for article in result_json['items']:
        article = clean_xml(article)
        article_soup = BeautifulSoup(article, 'xml')
        print('        * ', article_soup.title1.string)
        article_link_list.append('http://weixin.sogou.com' +
                                 article_soup.url.string)
    return article_link_list


def clean_xml(xml_str):
    xml_str = xml_str.rstrip('\n')
    replaces = (
        ('<?xml version="1.0" encoding="gbk"?>',
         '<xml version="1.0" encoding="gbk">'),
        ('\\', ''),)

    for from_str, to_str in replaces:
        xml_str = xml_str.replace(from_str, to_str)

    if not xml_str.endswith('</xml>'):
        xml_str += '</xml>'

    return xml_str


def queryset_iterator(queryset, chunk_size=100):
    """
    Iterate over a Django Queryset ordered by the primary key
    This method loads a maximum of chunk size (default: 100) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not pre_load all the
    classes.
    Note that the implementation of the iterator does not support ordered query
    sets.
    :param chunk_size: maximum of chunk
    :param queryset: query that want to query
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunk_size]:
            pk = row.pk
            yield row
        gc.collect()


def clean_title(article_title):
    if not article_title:
        return
    article_title = str(article_title, 'utf-8')
    article_title = article_title.strip()
    article_title = article_title.translate(tbl)
    return article_title
