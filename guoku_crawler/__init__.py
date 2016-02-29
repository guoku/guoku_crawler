# -*- coding: utf-8 -*-
import redis
import guoku_crawler.config


r = redis.Redis(host=config.CONFIG_REDIS_HOST,
                port=config.CONFIG_REDIS_PORT,
                db=config.CONFIG_REDIS_DB)
