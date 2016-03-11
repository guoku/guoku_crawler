#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from guoku_crawler.common.storage.encoding import Promise
from guoku_crawler.common.storage.encoding import force_unicode
from guoku_crawler.db import session


def smart_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a text object representing 's' -- unicode on Python 2 and str on
    Python 3. Treats bytestrings using the 'encoding' codec.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, Promise):
        # The input is the result of a gettext_lazy() call.
        return s
    return force_unicode(s, encoding, strings_only, errors)


def get_or_create(model, **kwargs):
    # Looks up an object with the given name, creating one if necessary.
    assert kwargs is not None
    try:
        instance = session.query(model).filter_by(**kwargs).first()
        return instance, False
    except MultipleResultsFound as e:
        instance = session.query(model).filter_by(**kwargs).first()
        logging.error("duplicate articles, title: %s."
                      " will use the first one. %s", kwargs['title'], e)
        return instance, False
    except NoResultFound as e:
        try:
            if session.autocommit:
                session.begin()  # begin
            else:
                session.begin(nested=True)  # savepoint
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            return instance, True
        except IntegrityError:
            session.rollback()  # rollback or rollback to savepoint
            instance = session.query(model).filter_by(**kwargs).one()
            return instance, False
