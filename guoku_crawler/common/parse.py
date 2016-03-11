#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup


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
    start_index = xml_str.find('<DOCUMENT>')
    xml_str = xml_str[start_index:]

    replaces = (
        ('?>', '>'),
        ('\\', ''),
        ('\n', '')
    )

    for from_str, to_str in replaces:
        xml_str = xml_str.replace(from_str, to_str)

    return xml_str
