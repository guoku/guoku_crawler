#!/usr/bin/env bash
set -e
case $1 in
    worker)
    exec celery -A guoku_crawler worker -l info
    ;;

    cookie_worker)
    exec celery -A guoku_crawler worker -l info -Q cookies
    ;;

    beat)
	exec celery -A guoku_crawler beat -l debug
    ;;

    flower)
    exec flower -A guoku_crawler --auto_refresh=True --address=0.0.0.0 --port=5555 --basic-auth=guoku:guoku1@#
    ;;

    *)
    exec "$@"
    ;;
esac
